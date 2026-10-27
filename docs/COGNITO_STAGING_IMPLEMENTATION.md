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

## Verified staging checkpoint (2026-10-22)

- GitHub CI run #71 passed after the initial-profile-role migration fix: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39642137364.
- Staging ECR image build #4 passed for commit `0174c50b992222d01a87bea0f323e9196ddd511d`: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39642644236. Image tag: `cognito-staging-0174c50b992222d01a87bea0f323e9196ddd511d`.
- Vercel reports a Ready preview deployment for this branch head, with branch alias `enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app`. Before using it, confirm the latest staging deployment still has this alias.
- Candidate staging callback URL: `https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/auth/callback`. Candidate sign-out URL: `https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/login`. These routes match the Next.js callback handler; the old CloudFront root did not.
- The Cognito managed-login page opened and a newly created Cognito user authenticated, but the manual test started at Cognito's hosted page and returned to the CloudFront root. That did **not** exercise the application's state/nonce/PKCE callback or the backend account-link endpoint.
- The Vercel environment-variable inventory shows shared Production/Preview variables for Supabase URL, Supabase anon key, and API URL, but no branch-specific Preview overrides for `cognito-staging-integration`. Do not turn Cognito on for this preview until branch-specific values point to the staging Supabase project and a separate staging backend; otherwise Preview may call Production services.
- Staging Supabase migration audit: all 19 migrations recorded; 16/16 public tables have RLS enabled; zero remaining `auth.uid()` references in public/storage policies; 25 policies use `public.current_profile_id()`; unmapped Cognito subjects resolve to NULL; the identity mapping table has no client policies or anon/authenticated table privileges, while `service_role` retains select/insert.
- Applied `20261022000001_restrict_role_scoped_rls_policies.sql` to staging. It removes public-read access to profiles, scopes the old "service role full access" policies to `service_role`, fixes the profile-insert policy scope, and closes the direct-Supabase interview privilege path: the old `FOR ALL USING (true)` policy and table grants let any authenticated browser session mutate all interviews, while this UI uses FastAPI routes (management-protected scheduling and authenticated candidate response). Live SQL verification confirms authenticated table privileges are revoked and only `service_role` remains on the interviews policy.
- RLS review found no other `USING (true)` data policy reachable by `anon` or `authenticated` with actual table privileges on this staging schema. Onboarding tables that do grant authenticated privileges have role-checked management policies or employee-owned row checks; knowledge chat ownership policies are profile-mapping-aware.
- Added and applied `20261022000000_harden_trigger_functions.sql` after the Supabase security advisor flagged trigger-only functions. It revokes direct RPC execution on `handle_new_user`, `set_updated_at`, and `log_onboarding_history` from `PUBLIC`, `anon`, and `authenticated`, and pins their search paths. Live SQL checks confirm the client roles cannot execute `handle_new_user` or `log_onboarding_history` and all three trigger functions have fixed search paths.
- Remaining Supabase security advisory is expected for the `current_profile_id()` and `get_current_user_role()` SECURITY DEFINER helpers, which are used by RLS expressions; the migration mapping table's RLS-without-policy INFO finding is intentional (service-role-only access). Performance advisor warnings include baseline missing FK indexes, auth RLS initplan suggestions, and policies/index usage; don't broadly rewrite existing app policies as part of Cognito setup without separate regression testing.
- The Cognito third-party integration is shown enabled in the dashboard, and the pre-token-generation Lambda is attached with `V2_0`; its mock test passed. Real Supabase acceptance of a Cognito JWT and real application callback/account linking have not yet been verified.

## Latest verified checkpoint (2026-10-22, run #85)

- Latest observed service-replacement CI run: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39723988185 — **success** at commit `b3be0587d1bf910e2fe0086ac1be35266349e46b`. The job covered frontend build, backend compile/tests, Cognito pre-token handler tests, PostgreSQL RLS/mapping/trigger-function regression checks, and CloudFormation template linting.
- The PR remains draft: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3.
- Live staging database hardening was applied and re-audited: 19 migrations recorded; 16/16 public tables have RLS; the identity mapping table is private to service_role; 25 policies use current_profile_id(); trigger-only functions have fixed search_path and no direct anon/authenticated EXECUTE.
- The Cognito callback handler at `frontend/app/auth/callback/route.ts` requires `COGNITO_REDIRECT_URI` to be an HTTPS URL whose path is exactly `/auth/callback`, validates state and required PKCE/nonce/redirect cookies, exchanges the authorization code, calls `COGNITO_LINK_API_URL`, and only then redirects to `/dashboard`.
- The actual manual login test was started directly from Cognito managed login and returned to the CloudFront root with `?code=...`, showing the generic Cognito success page. This did not exercise the Next.js callback route; treat the callback as **not yet tested**.
- Vercel's branch preview deployment is Ready on the stable alias `https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app`. Branch-scoped Preview overrides are now configured for `cognito-staging-integration`: `NEXT_PUBLIC_SUPABASE_URL` and the browser-safe publishable key target `workplace-assistant-staging`; `NEXT_PUBLIC_API_URL=https://example.invalid` intentionally fails closed until a separate staging API exists. These values apply only to Preview for this branch; shared Production variables remain untouched.
- Cognito mode remains **off** in Vercel Preview. After the staging API exists, configure Preview variables for this branch: `NEXT_PUBLIC_AUTH_PROVIDER=cognito`, the exact Cognito managed-login origin as `COGNITO_DOMAIN`, `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`, `COGNITO_REDIRECT_URI=https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/auth/callback`, `COGNITO_SIGN_OUT_URI=https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/login`, and `COGNITO_LINK_API_URL` for the staging API's `/api/v1/auth/cognito/link` endpoint. Set any refresh-token lifetime to the actual app-client configuration, not a guessed value. A new Preview deployment is required for env changes to take effect; do not change shared Production variables.
- The latest ECR image build (#4) remains successful for backend commit `0174c50b992222d01a87bea0f323e9196ddd511d`. Later changes have been migration/test/docs/infrastructure-only and did not alter backend runtime source, but rebuild if runtime code changes before deployment.
- S3 remains opt-in and not deployed. Production remains unchanged.

## AWS/Supabase steps required for staging

1. Confirm the Cognito app client uses Cognito user-pool authentication, authorization-code grant, `openid` and `email` scopes, and no client secret.
2. Register the staging branch's actual Vercel Preview callback URL (the HTTPS origin plus `/auth/callback`) as an allowed callback, and the same origin plus `/login` as an allowed sign-out URL. Select the `/auth/callback` URL as the default redirect URI. Do not use the old CloudFront root `https://d84l1y8p4kdic.cloudfront.net/` as the OAuth callback: the observed sign-in returned to Cognito's generic success page instead of the Next.js callback handler. Initiate real app sign-in from the staging app's `/login` route so the PKCE verifier, state, and nonce cookies are set.
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


## Cognito deletion lifecycle synchronization (staging)

- A successful Cognito `AdminDeleteUser` or `DeleteUser` event is routed by EventBridge/CloudTrail to `CognitoUserDeleteSyncFunction` in the staging CloudFormation template.
- The handler matches only the configured staging pool and an existing `cognito_identity_mappings` row. Cognito `sub` is the primary key; username matching is used only when no subject exists and the event time is older than the current mapping's last-verified time. This protects a newly recreated same-email account from a delayed event for the old account.
- The cleanup Lambda deletes the linked Supabase Auth user through the Auth Admin API and verifies the related `profiles` row and mapping disappear. `auth.users` deletion cascades those identity rows; job postings and application records remain because owner/user references use `ON DELETE SET NULL`.
- An EventBridge schedule runs reconciliation every 15 minutes to catch best-effort CloudTrail delivery gaps. It first completes a paginated `ListUsers` read, then deletes only mapping-linked Supabase Auth users whose `cognito_sub` is absent from the configured pool. Failed invocations retry and route to an encrypted SQS dead-letter queue.
- Additive staging Supabase migrations: `20261027000000_cognito_username_delete_sync.sql` and `20261027000001_keep_cognito_mapping_with_auth_identity.sql`. Both have been applied to the isolated staging project.
- **Deployment gate:** ECR build, focused regression tests, CloudFormation change-set review and live Cognito-delete acceptance test must pass before claiming end-to-end behavior. The AWS stack has not yet been updated to the new image/template at this checkpoint. Preserve Production/main and all job postings.
