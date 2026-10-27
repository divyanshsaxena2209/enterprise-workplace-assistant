-- Staging Cognito lifecycle cleanup needs stable identifiers because CloudTrail
-- may expose a Cognito subject or username depending on the delete operation.
ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_username text;

ALTER TABLE public.cognito_identity_mappings
    ADD COLUMN IF NOT EXISTS cognito_user_pool_id text;

-- Existing mappings in this isolated Supabase staging project belong to its
-- configured staging pool; backfill them so console deletions can be correlated.
UPDATE public.cognito_identity_mappings
SET cognito_user_pool_id = 'ap-south-1_89s6YRnwQ'
WHERE cognito_user_pool_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS cognito_identity_mappings_username_unique
    ON public.cognito_identity_mappings (lower(cognito_username))
    WHERE cognito_username IS NOT NULL;
