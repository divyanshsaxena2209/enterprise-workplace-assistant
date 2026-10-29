-- Restrict privileged service-role policies to the actual service_role database role.
-- Several original policies were named "service role full access" but had no TO
-- clause, which defaults to PUBLIC. Most corresponding tables currently have no
-- direct browser grants, but keeping these policies role-scoped prevents a future
-- grant from silently exposing unrestricted rows.

DROP POLICY IF EXISTS "Allow service role full access to status history" ON public.application_status_history;
CREATE POLICY "Allow service role full access to status history"
    ON public.application_status_history FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to applications" ON public.applications;
CREATE POLICY "Allow service role full access to applications"
    ON public.applications FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to scores" ON public.candidate_scores;
CREATE POLICY "Allow service role full access to scores"
    ON public.candidate_scores FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to candidates" ON public.candidates;
CREATE POLICY "Allow service role full access to candidates"
    ON public.candidates FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to resumes" ON public.resumes;
CREATE POLICY "Allow service role full access to resumes"
    ON public.resumes FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to jobs" ON public.jobs;
CREATE POLICY "Allow service role full access to jobs"
    ON public.jobs FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to recruiter notes" ON public.recruiter_notes;
CREATE POLICY "Allow service role full access to recruiter notes"
    ON public.recruiter_notes FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- Interviews are only managed by the authenticated, management-protected FastAPI
-- routes in this repository. The original PUBLIC policy plus GRANT ALL TO
-- authenticated allowed every signed-in user to read or mutate every interview.
DROP POLICY IF EXISTS "Allow full access to interviews" ON public.interviews;
REVOKE ALL ON TABLE public.interviews FROM anon, authenticated;
CREATE POLICY "Allow service role full access to interviews"
    ON public.interviews FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- Profiles contain personal data; remove the unrestricted public-read policy.
-- Own-profile and database-backed management policies remain in place.
DROP POLICY IF EXISTS "Allow public read access to profiles" ON public.profiles;

-- The service-role profile-insert policy was also accidentally scoped to PUBLIC.
DROP POLICY IF EXISTS "Allow service role to insert profiles" ON public.profiles;
CREATE POLICY "Allow service role to insert profiles"
    ON public.profiles FOR INSERT TO service_role
    WITH CHECK (true);
