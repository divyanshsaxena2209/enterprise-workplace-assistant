-- Staging-only permission fix for Cognito login callbacks.
-- link_verified_identity refreshes these mapping fields after token validation.
-- Keep this grant narrowly scoped; the service-role key remains server-side.
GRANT UPDATE ON TABLE public.cognito_identity_mappings TO service_role;
