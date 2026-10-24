-- Harden trigger-only functions in the staging schema.
-- Trigger invocations do not require callers to have EXECUTE on the trigger
-- function; direct PostgREST/RPC execution is not part of the application API.

ALTER FUNCTION public.handle_new_user()
  SET search_path = pg_catalog, public, auth, pg_temp;

ALTER FUNCTION public.set_updated_at()
  SET search_path = pg_catalog, public, auth, pg_temp;

ALTER FUNCTION public.log_onboarding_history()
  SET search_path = pg_catalog, public, auth, pg_temp;

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.set_updated_at() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.log_onboarding_history() FROM PUBLIC, anon, authenticated;
