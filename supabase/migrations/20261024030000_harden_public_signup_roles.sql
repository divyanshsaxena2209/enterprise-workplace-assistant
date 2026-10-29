-- User metadata is controlled by public signup requests and must never select
-- a privilege level or company-issued employee ID. raw_app_meta_data is managed
-- by trusted Auth administration and is the only accepted source for Management.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $function$
DECLARE
    assigned_role text;
    management_verified boolean;
BEGIN
    assigned_role := CASE
        WHEN upper(btrim(COALESCE(NEW.raw_app_meta_data->>'role', ''))) = 'MANAGEMENT'
            THEN 'MANAGEMENT'
        ELSE 'EMPLOYEE'
    END;

    management_verified := assigned_role = 'MANAGEMENT'
        AND COALESCE((NEW.raw_app_meta_data->>'is_management_verified')::boolean, false);

    INSERT INTO public.profiles (
        id, email, full_name, role, employee_id, department,
        job_title, phone, location, bio, avatar_url, is_management_verified
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        assigned_role,
        NULL,
        NEW.raw_user_meta_data->>'department',
        NEW.raw_user_meta_data->>'job_title',
        NEW.raw_user_meta_data->>'phone',
        NEW.raw_user_meta_data->>'location',
        NEW.raw_user_meta_data->>'bio',
        NEW.raw_user_meta_data->>'avatar_url',
        management_verified
    );

    RETURN NEW;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;
