-- The backend service role accesses profiles only through trusted FastAPI routes.
-- RLS policies do not replace PostgreSQL table grants. Keep these grants scoped
-- to service_role; anon/authenticated must not gain a direct Data API read/write path.
GRANT SELECT, INSERT, UPDATE ON TABLE public.profiles TO service_role;
