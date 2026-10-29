-- Keep the Cognito subject mapping attached to the Supabase Auth identity,
-- not the public profile row. Deleting/rebuilding a profile must not orphan the
-- Cognito mapping while auth.users still exists. Deleting auth.users still
-- cascades the mapping and the dependent public profile.
ALTER TABLE public.cognito_identity_mappings
    DROP CONSTRAINT IF EXISTS cognito_identity_mappings_profile_id_fkey;

ALTER TABLE public.cognito_identity_mappings
    ADD CONSTRAINT cognito_identity_mappings_profile_id_fkey
    FOREIGN KEY (profile_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;
