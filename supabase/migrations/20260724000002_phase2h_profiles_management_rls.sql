


CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS text AS $$
    SELECT role::text FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER;


DROP POLICY IF EXISTS "Allow management to read all profiles" ON public.profiles;
CREATE POLICY "Allow management to read all profiles"
    ON public.profiles FOR SELECT
    USING (public.get_current_user_role() IN ('MANAGEMENT', 'ADMIN', 'HR'));
