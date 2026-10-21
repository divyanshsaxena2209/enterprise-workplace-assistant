# Cognito staging integration: implementation notes

## Scope and safety

This is a staged authentication migration only. Do not change `main`, deploy Lambda, remove Supabase Auth, or migrate Supabase PostgreSQL. Keep Gemini and Qdrant unchanged.

Staging Cognito resources created in `ap-south-1`:
- User pool ID: `ap-south-1_89s6YRnwQ`
- Public app client ID: `7npkisjjm5jj0fsqf94et8lqra`
- Intended OAuth flow: authorization code grant with PKCE.
- Requested OIDC scopes: `openid email`.

Do not put secrets in source control. The app client must be a public client without a client secret.

## Findings from the current code

- `frontend/app/login/page.tsx` authenticates with `supabase.auth.signInWithPassword`.
- `frontend/app/signup/page.tsx` uses `supabase.auth.signUp` and submits profile metadata including role and employment fields.
- `frontend/lib/context/UserContext.tsx` loads the profile from Supabase `profiles` using the Supabase user UUID and obtains the access token from the Supabase session.
- `frontend/middleware.ts` delegates session handling to `frontend/lib/supabase/middleware.ts`, which calls `supabase.auth.getUser()`.
- FastAPI `backend/app/dependencies/auth.py` verifies a bearer token, reads its `sub`, and loads a profile by that ID through `ProfileRepository.get_by_id`.
- The current backend verifier in `backend/app/core/security.py` is for Supabase HS256 tokens.
- The Cognito RS256 access-token verifier lives in `backend/app/core/cognito_security.py`.
- `POST /api/v1/auth/cognito/link` requires both an existing valid Supabase session and a Cognito ID token with verified email that matches that existing profile.
- The additive migration `backend/migrations/20261021_cognito_identity_mappings.sql` creates a service-role-only mapping from Cognito `sub` to the existing Supabase profile UUID.
- The FastAPI middleware/dependency resolver supports Cognito access tokens only after `COGNITO_ENABLED=true` and after a valid profile mapping exists.

Therefore, adding a Cognito button or callback alone would not make Cognito sign-in work end-to-end: the frontend profile context, Next.js middleware, API bearer-token verification, and identity-to-existing-profile mapping all need to agree.

## Minimal safe implementation sequence

1. Add a separate Cognito OIDC verifier in FastAPI that validates the token signature against the User Pool JWKS and validates issuer, expiry, token type, and app-client audience/client ID. Keep Supabase verification supported during migration.
2. Define an explicit identity mapping between Cognito `sub` and the existing Supabase profile UUID. Do not assume Cognito `sub` equals the Supabase user UUID. Prefer a small mapping table in the existing Supabase PostgreSQL database; do not migrate the database. Establish mapping by a verified, unique email and an explicit linking/migration procedure, not by trusting arbitrary email claims from an unverified token.
3. Make the API resolve the mapped Supabase profile and continue to use its database-backed role. Never accept role claims or signup form fields as authority for Management access.
4. Add Cognito hosted-login initiation and callback using authorization code + PKCE, validating state and exchanging the code for tokens without any client secret.
5. Update the frontend session/context and middleware to support the staged Cognito session without breaking existing Supabase sessions. Preserve a rollback path.
6. Add integration tests for new Cognito sign-in, mapping, expired/invalid token rejection, employee/manager authorization, and existing Supabase sign-in.
7. Only after staging passes, register the exact production Vercel callback/sign-out URLs and plan a controlled cutover.

## Cognito redirect note

The app's callback route has not yet been implemented. Do not save a guessed callback URL in Cognito. The final registered callback must exactly match the implemented route and the `redirect_uri` used by the authorization request. Use HTTPS on Vercel. Do not assume the existing CloudFront URL is a valid callback until its ownership and behavior are confirmed.

## Not yet implemented by this document

This file documents verified dependencies and guards against an incomplete callback-only change. It does not implement Cognito login, create the mapping table, change AWS configuration, or deploy anything.


## Frontend and managed-login flow now in the staging branch

The opt-in frontend flow is gated by `NEXT_PUBLIC_AUTH_PROVIDER=cognito`. With that variable unset, the existing Supabase login/signup and middleware remain the default. The Cognito callback uses authorization code + PKCE, validates state, verifies the ID-token nonce at the backend, keeps tokens in HttpOnly cookies, and provisions only Employee profiles when the verified Cognito email has no existing profile. Roles are never accepted from browser signup metadata.

### Required Vercel preview environment values

Set these only on a branch Preview environment after a staging API exists. Do not set them on Production yet.

- `NEXT_PUBLIC_AUTH_PROVIDER=cognito`
- `NEXT_PUBLIC_API_URL`: the staging Lambda Function URL/API base URL. Use the exact value already used by your frontend, but for the staging Lambda—not production.
- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`: the existing Supabase project URL and browser-safe anon/publishable key.
- `COGNITO_DOMAIN`: the exact HTTPS domain shown under Cognito User Pool → Branding/Domain; do not use the sample CloudFront callback.
- `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`
- `COGNITO_REDIRECT_URI`: the exact HTTPS Vercel Preview URL followed by `/auth/callback`.
- `COGNITO_SIGN_OUT_URI`: the same Preview origin followed by `/login`; register this exact URL as an allowed sign-out URL.
- `COGNITO_LINK_API_URL`: the staging backend's full HTTPS `/api/v1/auth/cognito/link` endpoint.
- `COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS`: set to the refresh-token lifetime configured on the Cognito app client (seconds).

No client secret belongs in the browser or this repository. The browser-based app client must remain a public client with authorization code grant and PKCE.

### Required Cognito and Supabase settings before a live test

1. In the Cognito app client, register the exact Preview callback and sign-out URLs above. Keep Cognito user pool as the identity provider, Authorization code grant selected, and the `openid` and `email` scopes selected.
2. In Supabase Dashboard → Authentication → Third-Party Auth, add AWS Cognito with User Pool ID `ap-south-1_89s6YRnwQ` and region `ap-south-1`.
3. Deploy `infra/cognito/pre-token-generation/index.mjs` as a small Node.js Lambda and attach it to the user pool's Pre token generation trigger using event version `V2_0`. This adds Supabase's infrastructure claim `role=authenticated` to Cognito ID and access tokens. It does **not** assign application-management privileges.
4. Apply `supabase/migrations/20261021000000_cognito_third_party_auth.sql` to a staging database first and review the generated policy changes. It adds a protected identity-mapping table and updates existing `auth.uid()` ownership expressions to resolve mapped Cognito identities to existing profile IDs, while falling back to `auth.uid()` for legacy Supabase Auth tokens.
5. On the staging backend only, set `COGNITO_ENABLED=true`, `COGNITO_REGION=ap-south-1`, `COGNITO_USER_POOL_ID=ap-south-1_89s6YRnwQ`, and `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`.
6. Run existing Supabase sign-in and Cognito sign-in against staging; verify employee RLS, manager RLS, profile mapping, signup provisioning and sign-out. Do not change Production Vercel variables or production Lambda until these tests pass.

### Local automated coverage

GitHub Actions now runs the backend unit tests and a PostgreSQL integration test for the SQL migration, including mapped Cognito ownership, rejected unmapped subjects, legacy Supabase fallback, and Supabase Storage ownership policies. It also builds the Next.js frontend with harmless placeholder environment values. These are staging/code tests, not a claim that the live AWS or Supabase settings have been configured.
