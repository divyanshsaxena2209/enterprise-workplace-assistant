-- The API uses the service role for job reads, and its trusted service layer
-- filters employee results to PUBLISHED jobs. Do not grant browser roles direct access.
GRANT SELECT ON TABLE public.jobs TO service_role;
