-- Staging Cognito lifecycle cleanup requires a stable username fallback
-- because a delete event may contain the Cognito username instead of the subject.
ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_username text;

CREATE UNIQUE INDEX IF NOT EXISTS cognito_identity_mappings_username_unique
    ON public.cognito_identity_mappings (lower(cognito_username))
    WHERE cognito_username IS NOT NULL;
