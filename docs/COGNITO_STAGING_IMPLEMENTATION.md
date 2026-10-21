# Cognito staging integration

## Scope and safety

This change is an opt-in staging path. The existing Supabase Auth login/signup, Supabase PostgreSQL, Gemini, and Qdrant remain the default/active services. Do not change Production Vercel variables, Production Lambda, the Supabase Production schema, or merge this PR until real staging login and regression checks pass.

Staging Cognito identifiers:
- Region: `ap-south-1`
- User pool ID: `ap-south-1_89s6YRnwQ`
- App client ID: `7npkisjjm5jj0fsqf94et8lqra`
- OAuth: authorization code grant + PKCE
- OIDC scopes: `openid email`
- Cognito remains disabled in the backend unless `COGNITO_ENABLED=true`.

## What is implemented in the branch

- FastAPI validates Cognito access tokens with RS256/JWKS, issuer, expiry, `token_use=access`, and app client ID. A separate ID-token verifier checks signature, issuer, expiry, audience/app client, `token_use=id`, verified email, and the OAuth nonce.
- The API resolves Cognito `sub` through `public.cognito_identity_mappings` to the existing `public.profiles.id`; the application's role/active status is read from the existing profile row, never from Cognito claims.
- The account-link/provision endpoint verifies Cognito ID-token claims and checks any existing profile's email against the corresponding Supabase Auth user record. New public signups are provisioned as `EMPLOYEE` server-side; browser profile fields cannot assign a role.
- The additive migration `supabase/migrations/20261021000000_cognito_third_party_auth.sql` creates a service-role-only mapping table, maps existing `auth.uid()` RLS ownership checks to a linked profile ID for Cognito issuers, and leaves the legacy Supabase Auth `auth.uid()` behavior unchanged.
- The pre-token-generation V2_0 Lambda handler adds Supabase's infrastructure claim `role=authenticated` to Cognito JWTs. It does not grant application `MANAGEMENT` privileges.
- The frontend's Cognito flow is gated by `NEXT_PUBLIC_AUTH_PROVIDER=cognito`. If unset, legacy Supabase authentication remains selected. The Cognito flow uses authorization code + PKCE, state and nonce, server-set HttpOnly cookies, refresh, logout, and the API token resolver.
- CI runs the backend tests, PostgreSQL migration/RLS integration test, Node.js pre-token-trigger tests, and Next.js frontend build.
- The direct API calls for job creation/publication and interview scheduling now select the Cognito access token when Cognito mode is enabled instead of assuming a Supabase Auth session exists.

## Preview configuration needed before a live sign-in test

Only set these in a **Vercel Preview** environment after confirming that a separate staging API is available. Do not set them in Production.

- `NEXT_PUBLIC_AUTH_PROVIDER=cognito`
- `NEXT_PUBLIC_API_URL`: staging backend base URL, not the existing Production API.
- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`: existing Supabase project URL and browser-safe anon/publishable key. Do not use the service-role key here.
- `COGNITO_DOMAIN`: exact HTTPS Cognito managed-login domain shown in the user pool's domain/branding settings.
- `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`
- `COGNITO_REDIRECT_URI`: exact HTTPS Preview origin plus `/auth/callback`.
- `COGNITO_SIGN_OUT_URI`: exact Preview origin plus `/login`.
- `COGNITO_LINK_API_URL`: full HTTPS staging backend endpoint ending `/api/v1/auth/cognito/link`.
- `COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS`: refresh-token lifetime configured on the app client, in seconds.

Never create or expose a browser client secret. Cognito must use a public app client with authorization-code grant and PKCE.

## AWS/Supabase steps required for staging

1. Confirm the Cognito app client uses Cognito user-pool authentication, authorization-code grant, `openid` and `email` scopes, and no client secret.
2. Register the exact Vercel Preview `/auth/callback` URL as an allowed callback and the exact Preview `/login` URL as an allowed sign-out URL. Select the callback as the default redirect URI. Keep the existing CloudFront URL until we confirm it is unnecessary.
3. In Supabase Dashboard → Authentication → Third-Party Auth, add Amazon Cognito using user pool `ap-south-1_89s6YRnwQ` and region `ap-south-1`.
4. Deploy `infra/cognito/pre-token-generation/index.mjs` as a small Node.js Lambda and attach it to the Cognito user pool's Pre token generation trigger using event version `V2_0`.
5. Apply `supabase/migrations/20261021000000_cognito_third_party_auth.sql` to a **staging Supabase project first**. Review the RLS policy rewrite before applying: it changes ownership checks that call `auth.uid()` in `public` and `storage` so mapped Cognito subjects resolve to their existing profile IDs. Unmapped Cognito subjects resolve to no profile; existing Supabase JWTs retain their old behavior.
6. Create or identify a **separate staging backend deployment** before setting its Cognito environment variables: `COGNITO_ENABLED=true`, `COGNITO_REGION=ap-south-1`, `COGNITO_USER_POOL_ID=ap-south-1_89s6YRnwQ`, and `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`. Keep the current production Lambda configuration unchanged.
7. Run live tests in Preview/staging: Cognito sign-in and signup, existing-account mapping, new employee provisioning, employee and manager route permissions, Supabase table and storage RLS, token refresh, logout, and the existing Supabase login. Do not perform a production cutover until all pass.

## Validation boundary

GitHub Actions run #58 passed for the commit associated with the current staging branch at that time. That run shows automated tests and the frontend build passed; it does not prove the actual AWS Lambda trigger, Supabase Third-Party Auth integration, staging environment variables, real browser login, or production ECR registry state.

The PR must remain draft until staging configuration and live end-to-end tests pass.
