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
- Employee-ID assignment is handled inside FastAPI at `PATCH /api/v1/profile/employees/{profile_id}/employee-id`. It requires a database-backed management role and validates that the target row is an employee. The old Next.js service-role mutation route is removed so Vercel does not need a Supabase service-role key.

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

GitHub Actions run #68 passed for commit `9b1fab677bf43c810f8e33dc2b7bd6f953b8377e`: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39621760819. It verifies the frontend build, backend tests, Cognito token/identity tests, PostgreSQL migration/RLS integration tests, and pre-token trigger tests. It does not prove the actual AWS Lambda trigger, Supabase Third-Party Auth integration, staging environment variables, real browser login, or staging ECR image publication.

The PR must remain draft until staging configuration and live end-to-end tests pass.


## Isolated backend image for Cognito staging

The branch workflow `.github/workflows/build-cognito-staging-ecr.yml` builds the backend from this branch and pushes only a unique ECR tag:
`745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-<commit-sha>`.

It does not push `latest`, update the production Lambda function, or change its environment. Use this exact staging-tagged image only when creating a separate staging Lambda function. The workflow uses a dedicated `GitHubActions-EWA-Cognito-Staging-ECR` role, not the existing production deployment role. Its trust policy must be scoped to this repository and the `cognito-staging-integration` branch; do not broaden permissions beyond the ECR repository push actions listed below.

The staging Lambda should use separate staging configuration and a staging database/project. Do not point a Cognito-preview signup flow at Production Lambda, because the new-user linking endpoint provisions profile records.


## Required IAM role to build the staging image

The staging image workflow intentionally does not use the existing `GitHubActions-EWA-Deploy` role, because that role is used by the production build path and does not trust this staging ref. Create a separate role with only ECR push permissions before rerunning the staging image workflow.

### Trust policy

Create an IAM role named `GitHubActions-EWA-Cognito-Staging-ECR` with **Web identity** as the trusted entity. Select the existing OIDC provider `token.actions.githubusercontent.com` and audience `sts.amazonaws.com`, then ensure its trust relationship uses this exact repository/branch subject (keep the audience condition too):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::745531385877:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:divyanshsaxena2209/enterprise-workplace-assistant:ref:refs/heads/cognito-staging-integration"
        }
      }
    }
  ]
}
```

### Inline ECR policy

Attach this inline policy to that role. It can push only to the existing backend ECR repository; it cannot update Lambda or change production infrastructure.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRLogin",
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Sid": "PushOnlyToBackendRepository",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": "arn:aws:ecr:ap-south-1:745531385877:repository/enterprise-workplace-assistant-backend"
    }
  ]
}
```

After creating the role, open the [staging ECR workflow](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml), select branch `cognito-staging-integration`, and choose **Run workflow**. Expected output image tag is `cognito-staging-<commit-sha>`. This workflow never pushes `latest` and never updates a Lambda function.
