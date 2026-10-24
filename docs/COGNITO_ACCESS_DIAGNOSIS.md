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


## Migration continuation checkpoint — 25 October 2026

### Verified completed
- Branch `cognito-staging-integration` includes the Employee/Management signup choice, safe requested-role validation, management access request workflow, server-only approval table/function, management-only review endpoints, Settings access inbox, and a trusted-email allowlist for the initial Management account.
- On branch SHA `0b611348e6798fc5f79872f2b63dab7562228c07`, GitHub Actions run [#40124001477](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40124001477) passed: the backend/frontend build and compile checks, CloudFormation lint, Cognito trigger tests, and service-replacement test suite succeeded (109 tests, 10 warnings).
- Applied the additive migration `20261025000000_management_access_requests.sql` to the **staging** Supabase project `wxulxcsdpwsyhtpkbazi` only. The migration history now records version `20261024191143`, name `management_access_requests`.
- Read-only SQL verification confirms `public.management_access_requests` exists with RLS enabled; `anon` and `authenticated` cannot SELECT the table or execute `review_management_access_request`; `service_role` can SELECT/INSERT and execute the database review function; request count is currently zero. The Security Advisor reports the expected INFO finding for a private RLS table with no client policies, alongside the pre-existing Cognito identity-table INFO and pre-existing SECURITY DEFINER warnings for `current_profile_id()` and `get_current_user_role()`. No new public execution warning was reported for the request-review function.
- Read-only Vercel inspection shows the Preview branch environment is set to Cognito, the staging Supabase project, the branch `/auth/callback` and `/login` URLs, and a staging Lambda Function URL for API/link calls. The latest inspected Ready Preview is SHA `d7c4765113c1259e20c1fd7a52c229e2a39690a0` (the frontend source commit); the subsequent `0b611348...` change only moved a backend migration-test fixture.
- The staging database still has one Cognito-linked active profile with role `EMPLOYEE`; it has not yet received Management privileges. This accurately explains the prior “Cognito created the account but app access was missing” symptom: identity proof/linking is not the same as the profile's application role.

### Current unverified items
- A follow-up hardening commit (`5c143e8...` plus the test-fixture fix at `9c091bbb...`) requires a fresh green CI run before the branch is considered validated. At the last check, GitHub was still running the frontend build for those commits. The preceding full suite passed, but do not describe the newest commits as green until their own run completes.
- AWS stack/image/environment state could not be inspected from the connected tools. A read-only health request to the configured Lambda URL could not be reached from this environment, so the current backend runtime is **not verified to include these source changes**.
- No ECR image was built or pushed for the newest source. The ECR workflow is deliberately manual-only.
- No end-to-end browser test has yet confirmed Cognito callback → PKCE/code exchange → identity link → `/api/v1/auth/me` → protected route authorization with the currently deployed Lambda.

### Management access model and initial admin
- The signup page now asks **Employee** or **Management**.
- Employee self-signup is assigned `EMPLOYEE`.
- Management is assigned immediately only if Cognito's **verified email** is on the server-side `COGNITO_MANAGEMENT_EMAIL_ALLOWLIST` (a comma-separated CloudFormation parameter on the isolated staging Lambda template). Otherwise the request is saved and an already active Management profile must approve it.
- The allowlist is the safe bootstrap path for the first manager because an empty system has no existing Management user to approve the first request. Set this only to the intended verified manager email in the staging stack. Do not commit the email or any secrets into GitHub. The profile database role is authoritative; Cognito user attributes and browser form fields cannot elevate roles.
- AWS IAM remains for Lambda execution (logs and the scoped private S3 prefixes) and GitHub OIDC/ECR publishing. Employees and Managers do not get AWS access keys or direct S3 IAM permissions.

### Remaining release gate
1. Confirm the latest CI run is green for the current branch head.
2. Manually dispatch `.github/workflows/build-cognito-staging-ecr.yml` from the verified current branch. This produces a new immutable staging ECR tag; it may incur small ECR storage/request charges, so retain the existing cost guard.
3. In AWS, update **only** the existing isolated staging CloudFormation stack with the image tag from that successful run and set `ManagementEmailAllowlist` to the intended verified first-manager email. Preserve the existing staging Supabase secret using CloudFormation's previous-value path or enter it directly as a `NoEcho` parameter. Do not change Production.
4. Redeploy/verify the Cognito branch Preview against the updated staging API, then run the consolidated sign-in/callback/profile/role test. Test an Employee-only action and a Management-only action with an allowlisted Manager; also verify that a non-allowlisted Management request remains Employee until approval.
5. Once staging E2E passes, proceed with the S3 opt-in storage cutover and CloudWatch runtime/alarms review. S3 still defaults to Supabase; no bucket was created and no Production resources were changed.
