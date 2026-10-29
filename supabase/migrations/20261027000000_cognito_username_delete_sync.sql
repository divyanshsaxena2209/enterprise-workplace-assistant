-- Staging Cognito lifecycle cleanup uses stable identifiers for deletion events.
ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_username text;

ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_user_pool_id text;

ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_last_verified_at timestamptz NOT NULL DEFAULT now();

-- Existing mappings in this isolated Supabase staging project belong to its
-- configured staging pool. Keep a fresh timestamp as the lifecycle baseline.
UPDATE public.cognito_identity_mappings
SET cognito_user_pool_id = 'ap-south-1_89s6YRnwQ',
    cognito_last_verified_at = COALESCE(cognito_last_verified_at, now())
WHERE cognito_user_pool_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS cognito_identity_mappings_username_unique
    ON public.cognito_identity_mappings (lower(cognito_username))
    WHERE cognito_username IS NOT NULL;
