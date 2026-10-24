# Cognito Access Diagnosis — 2026-10-25

Repository: `divyanshsaxena2209/enterprise-workplace-assistant`
Branch: `cognito-staging-integration`
Draft PR: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3

## Findings

The current branch already implements the important distinction between authentication and authorization:
- Cognito hosted sign-in/signup uses OAuth authorization code + PKCE and returns through `/auth/callback`.
- The callback exchanges the code, then calls `COGNITO_LINK_API_URL` to link/provision the identity.
- FastAPI validates Cognito access tokens against the user pool JWKS and checks issuer, expiry, `token_use=access`, and app client ID.
- The access token's Cognito `sub` must resolve through the server-only `cognito_identity_mappings` table to an existing `profiles.id`.
- The application role is loaded from the database profile, not from the user's editable Cognito attributes.
- The signup UI deliberately provisions self-service users as EMPLOYEE. It displays Management as administrator-assigned. Public signup must not permit self-selection of MANAGEMENT.
- The Cognito staging backend is a separate CloudFormation stack and is not the production Lambda. The frontend callback needs its exact HTTPS Preview URL and the account-link endpoint must point to the staging backend.

## Most likely access-denial boundary

The previous manual test reached Cognito's hosted page and authenticated, but returned to the CloudFront root instead of the app's `/auth/callback`. That does not process the PKCE/state/nonce flow or call the account-link endpoint. A user can therefore exist in Cognito and authenticate successfully while the application still has no linked profile or valid application session.

The current handoff explicitly says Vercel Preview had no branch-specific Cognito/staging overrides at the last audit. If preview uses the shared API URL or Production Supabase variables, do not enable Cognito mode there.

## Correct application role model

- Public self-sign-up: EMPLOYEE only.
- MANAGEMENT: assigned by an existing trusted administrator / server-side management workflow; never trust a client-submitted role or Cognito custom attribute for elevation.
- IAM roles: AWS workload/deployment permissions, not the app's Management/Employee permissions. Lambda gets a least-privilege execution role. GitHub Actions gets a separate ECR-publishing role. Employees/managers do not receive AWS credentials.
- Cognito Identity Pool IAM role mapping is only needed if users must obtain temporary AWS credentials for direct AWS access. This app should keep S3 private and mediate files through FastAPI; direct browser credentials are not needed for ordinary app access.

## Verified versus pending

- CI run #40121025445 for commit `d0d5beaca764532bf799f5bc2ae1770b7fb7d08d` succeeded on the Cognito staging branch. This is not evidence of a live end-to-end Cognito callback.
- Previous handoff reports a successful CI checkpoint with 67 tests and successful staging ECR build, plus staging Supabase migration/RLS audits.
- Live Cognito browser callback + identity link + protected endpoint test remains pending.
- Staging API stack is opt-in and potentially chargeable. Do not create it without an explicit cost gate and isolated staging service-role secret entered directly in AWS Console; never place secrets in chat or GitHub.
- S3 remains opt-in and defaults to Supabase Storage until the private bucket, execution-role access, and resume/knowledge smoke tests are verified.

## Consolidated staging acceptance test

After a staging API and Preview config are confirmed:
1. Start signup from the branch Preview's own signup page.
2. Confirm redirect URI is exactly the Preview origin plus `/auth/callback`.
3. Confirm callback validates state, exchanges code with PKCE, verifies nonce, and calls the staging account-link endpoint.
4. Confirm the linked profile is EMPLOYEE and `GET /api/v1/profile/me` (or the current profile endpoint) returns the mapped database profile.
5. Confirm a protected employee action succeeds, a Management-only action returns 403, and an unlinked Cognito subject returns 401/404 without creating a session.
6. Confirm refresh and logout, then run a separate Management test using an admin-provisioned account.
7. Confirm the test hit only the staging API and staging Supabase project.

Never test against Production or expose access/refresh tokens, OAuth codes, secrets, or presigned URLs in screenshots/logs.
