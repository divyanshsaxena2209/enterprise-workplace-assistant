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
