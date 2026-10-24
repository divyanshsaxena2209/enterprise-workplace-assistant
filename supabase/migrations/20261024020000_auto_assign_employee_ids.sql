-- Assign stable company IDs on the database side so every signup path
-- (including the Cognito/Supabase shadow-profile path) receives the same behavior.
-- Only blank IDs are generated; existing nonblank employee IDs and all roles are preserved.
CREATE SEQUENCE IF NOT EXISTS public.employee_id_seq;

-- Start after existing numeric IDs so the backfill does not have to walk through
-- the entire already-issued range. Restrict conversion to numeric suffixes that
-- safely fit in bigint; all other legacy formats are simply preserved.
SELECT setval(
    'public.employee_id_seq',
    COALESCE((
        SELECT MAX(
            CASE
                WHEN employee_id ~ '^EMP-[0-9]{1,18}$' THEN substring(employee_id FROM 5)::bigint
                WHEN employee_id ~ '^MGR-[0-9]{1,18}$' THEN substring(employee_id FROM 5)::bigint
            END
        )
        FROM public.profiles
    ), 0) + 1,
    false
);

CREATE OR REPLACE FUNCTION public.assign_employee_id()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $function$
DECLARE
    id_prefix text;
    generated_id text;
BEGIN
    IF NEW.employee_id IS NULL OR btrim(NEW.employee_id) = '' THEN
        id_prefix := CASE
            WHEN upper(btrim(COALESCE(NEW.role, ''))) IN (
                'MANAGEMENT', 'ADMIN', 'HR', 'HR_ADMIN', 'SUPER_ADMIN'
            ) THEN 'MGR-'
            ELSE 'EMP-'
        END;

        LOOP
            generated_id := id_prefix || lpad(nextval('public.employee_id_seq'::regclass)::text, 6, '0');
            EXIT WHEN NOT EXISTS (
                SELECT 1
                FROM public.profiles AS existing_profile
                WHERE existing_profile.employee_id = generated_id
                  AND existing_profile.id IS DISTINCT FROM NEW.id
            );
        END LOOP;

        NEW.employee_id := generated_id;
    END IF;

    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS profiles_assign_employee_id ON public.profiles;
CREATE TRIGGER profiles_assign_employee_id
BEFORE INSERT OR UPDATE OF employee_id ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.assign_employee_id();

-- The trigger runs with its owner's privileges; the sequence is not a browser API.
REVOKE ALL ON SEQUENCE public.employee_id_seq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.assign_employee_id() FROM PUBLIC, anon, authenticated;

-- Backfill incomplete existing profiles on this database, while keeping roles,
-- names, emails, and all other profile fields unchanged.
UPDATE public.profiles
SET employee_id = NULL
WHERE employee_id IS NULL OR btrim(employee_id) = '';
