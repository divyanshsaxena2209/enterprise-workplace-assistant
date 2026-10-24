-- Trusted FastAPI repositories use the service-role client. Keep grants scoped
-- to service_role and grant only the operations actually used by repository code.
-- Authorization/row filtering remains in the authenticated API/service layer.
GRANT SELECT, INSERT, UPDATE ON TABLE public.jobs TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.applications TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.candidates TO service_role;
GRANT SELECT, INSERT ON TABLE public.resumes TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.candidate_scores TO service_role;
GRANT SELECT, INSERT ON TABLE public.application_status_history TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.recruiter_notes TO service_role;

-- No browser-facing role receives direct access to these backend-only records.
REVOKE ALL ON TABLE public.applications, public.candidates, public.resumes,
    public.candidate_scores, public.application_status_history, public.recruiter_notes
FROM anon, authenticated;
