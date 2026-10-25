# CURRENT REQUIREMENTS OVERRIDE — 25 October 2026: four-service AWS integration

This section supersedes any conflicting older scope notes below. The user has clarified that **all four services must be integrated into the application as replacements for the existing equivalent capabilities**: **Amazon Cognito, AWS IAM, AWS Lambda, and Amazon CloudWatch**. Do not narrow the goal to Cognito/IAM only or label Lambda/CloudWatch out of scope. Keep work minimal and focused on a demonstrably working staging path; do not claim completion from source code or a successful image build alone.

## Required target architecture and acceptance criteria

1. **Amazon Cognito — application identity/authentication**
   - Use the staging Cognito User Pool for sign-up/sign-in, OAuth authorization-code + PKCE callback, token validation, session refresh/logout, and mapping Cognito subject to the existing application profile.
   - Employee/Management is an application authorization choice, not an AWS IAM identity. New users default to Employee. Outside the demo exception, Management requires the trusted verified-email allowlist or a Management approval flow; never trust a browser role choice. For the staging demo only, `COGNITO_DEMO_ROLE_SELECTION_ENABLED` defaults false and is effective only when `COGNITO_ENABLED=true` and `ENVIRONMENT=staging`; it deliberately enables self-service role switching for the demo and must never be enabled in Production.
   - Acceptance: real staging browser sign-in reaches `/auth/callback`, creates/loads the correct profile mapping, and protected API calls work.

2. **AWS IAM — permissions and least privilege**
   - IAM is integrated through service roles/policies, not by handing employees or managers AWS credentials. Verify the staging Lambda execution role, its permission to write CloudWatch logs, and only the resource access the backend actually requires. Verify the separate GitHub OIDC/ECR publishing role used by the manual image workflow.
   - Keep application `EMPLOYEE`/`MANAGEMENT` authorization in `public.profiles.role` and FastAPI route/data-scope checks. These are not interchangeable with AWS IAM.
   - Acceptance: roles have appropriate trust relationships and least-privilege policies; no public/browser AWS keys; denied operations stay denied.

3. **AWS Lambda — staging backend runtime**
   - The existing isolated stack is `ewa-cognito-staging-api` in `ap-south-1`; inspect/update this stack and its existing Lambda only. Never create a duplicate function or touch Production.
   - Verify the deployed container image URI/digest matches the successful current-branch ECR build, the environment points to the isolated staging Supabase project and correct Cognito configuration, the Function URL/API route responds, and the new Management access logic is in the running image.
   - Acceptance: live health/auth/profile endpoints work against staging. A built/pushed ECR image does not prove Lambda is running it.

4. **Amazon CloudWatch — runtime observability**
   - Integrate and verify Lambda log delivery, a bounded log-retention policy, and useful invocation/error/duration metrics. Confirm at least one real staging invocation can be correlated to sanitized logs. Add only minimal, cost-conscious monitoring needed for the migration; do not create paid dashboards/alarms unless cost and necessity are checked.
   - Acceptance: a staging invocation produces logs and metrics; errors can be diagnosed without logging tokens, passwords, authorization codes, or secrets.

## Scope and safety rules
- Main priority is the four services above and one end-to-end staging test covering the login-page Employee/Management selector, Cognito callback/profile mapping, role-bound authorization, refresh/logout, Lambda runtime, IAM configuration and one correlated CloudWatch log/metric.
- Keep the staging storage provider as Supabase while completing these four services; no S3 bucket creation or storage cutover is required to validate this four-service milestone. Track the previously requested S3 storage migration separately as a remaining requirement unless the user explicitly removes it.
- Do not modify Production, merge PR #3 before staging acceptance tests, use Production secrets, or share secrets in chat.
- Avoid unnecessary infrastructure, repeated console retries, unrelated refactors, dashboards, or other scope creep. If a manual AWS console step is required, ask for only the single next piece of evidence needed.

## Progress estimate as of 25 October 2026
Planning estimate, not measured code coverage:
- Cognito/source and role-flow implementation: **~85%**; real browser E2E still unverified.
- IAM integration: **~65%**; role templates/configuration exist, but live execution-role/policy alignment still needs verification.
- Lambda integration: **~75%**; isolated function/stack exists and an image was built, but the latest intended image and config were not confirmed deployed. The latest change-set console showed blank status metadata and a failed execution attempt; resolve by checking stack state/Events and current deployed image, not by repeatedly executing the same change set.
- CloudWatch integration: **~45%**; Lambda log-group/retention and automatic Lambda metrics are expected/configured in the template, but real runtime log delivery/correlation and alarms/alerts are not confirmed.
- Four-service staging E2E/release acceptance: **~25%** until a real browser session and one correlated invocation are demonstrated.
- Four-service overall: **~60–65%** as a rough weighted planning estimate. Do not present this as verified completion. S3 storage migration remains a separate, uncompleted item from the older broad migration plan.

## Immediate next actions — keep minimal
1. Inspect current AWS stack status and deployed Lambda image URI/digest (do not rely on stale handoff tags).
2. Inspect the current change-set list/stack Events for the exact failed-update status reason. If the AWS console still says “Failed to fetch,” use the stack's current Stack info/Resources and Lambda Image URI as independent evidence rather than refreshing repeatedly.
3. If the image/config is stale, build only from the current branch head and update the existing stack with the immutable tag actually produced by the successful workflow; preserve secret parameters using the console's previous-value/NoEcho handling.
4. Verify IAM execution role + CloudWatch log delivery; invoke a safe staging endpoint and inspect one sanitized log event.
5. Perform one consolidated staging browser test. Record exact observed pass/fail results here; keep PR #3 draft until accepted.

---

# Enterprise Workplace Assistant — Migration Continuation Handoff

**Purpose:** Current source of truth to paste into a new ChatGPT conversation. Verify live branch/resource state before making changes. This replaces the older October 21 snapshot where it conflicts with this document.


> **HISTORICAL SCOPE NOTE — superseded by the current four-service requirements at the top of this file.** Do not follow the older Cognito/IAM-only restriction below. The current requirement is to complete Cognito, IAM, Lambda, and CloudWatch integrations in staging; S3 migration stays separately deferred unless explicitly re-scoped.



## Latest source milestone — staging demo role selector (25 October 2026)

### Implemented on `cognito-staging-integration`
- Added an Employee/Management selector to the Cognito login page. The chosen level is preserved through the OAuth start flow in a short-lived HttpOnly cookie and passed to the backend only after the callback has validated OAuth state, nonce and PKCE.
- Added backend request schema support for the selected application access level.
- Added `COGNITO_DEMO_ROLE_SELECTION_ENABLED` and a strict server-side guard: demo role switching is active only when Cognito is enabled, the flag is explicitly true, and `ENVIRONMENT=staging`. Default is false. Do not enable it in Production.
- When enabled in the isolated staging demo, selecting Employee or Management changes the existing mapped `public.profiles.role` and `is_management_verified`. When disabled, the pre-existing safe flow remains: Employee by default, trusted server-side allowlist for immediate Manager bootstrap, or a Management access request requiring approval. Browser role selection never grants AWS IAM credentials.
- Added CloudFormation parameter `DemoRoleSelectionEnabled`, default `false`, with an environment variable mapping to `COGNITO_DEMO_ROLE_SELECTION_ENABLED`. It can be set to `true` only for the dedicated staging demo.
- Added regression tests for promotion/demotion by the staging demo selector and for the guard requiring the staging environment. CI run [#203](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40183230406) passed on `5696ffb411606c28f6e1c857babd208b4afb0141`: **115 tests passed, 10 warnings**. CloudFormation log wiring was then corrected by adding `LoggingConfig.LogGroup: !Ref StagingApiLogGroup`; the first lint run flagged a redundant explicit `DependsOn`, which was removed. CI run [#205](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40183594878) passed on template/source SHA `817f9bfc30d62c14b3f6e3ab81b56c180573b1f5`: **115 tests passed, 10 warnings**, frontend build, backend compile, and CloudFormation lint succeeded. The latest GitHub Vercel status on the login UI commit is green.

### Important current deployment facts
- User-confirmed successful earlier ECR build: workflow run #17 for commit `7d881ef`, tag `cognito-staging-7d881efbfb623e9b2f7d9f1f55b6257ff76922ea`, digest `sha256:b544a52a05be5473a2af70f43507791f2779b32500cd7cd6fa93442de19f7cec`.
- AWS Lambda was later inspected and still showed the OLD digest `sha256:fb2fe145a2821db094a0886927a7e80a2e617fb535ff61e7769bd8ba19039698`.
- The change set `ewa-cognito-hiz8yhphf7-ukxhbznvt4p` was created with the earlier image/template, before the demo-role selector code and `DemoRoleSelectionEnabled` parameter existed. **Do not execute that pending change set.** The last attempt to execute an older change set showed “Failed to execute change set,” but AWS Events could only be fetched for the prior 24 October operation; root failure is still unknown.
- These new source/template commits occurred after the successful image build. A **fresh manual ECR build from the final branch head is required**; the previous tag/image cannot contain the new login selector/backend flag. After a successful new build, create a fresh change set against the existing stack `ewa-cognito-staging-api`. Preserve both staging Supabase secret parameters with CloudFormation “Use previous value”; never paste them in chat.
- For the demo change set: set `ImageUri` to the immutable tag/digest from that new successful build, `DemoRoleSelectionEnabled=true`, leave `ManagementEmailAllowlist` blank (not needed in this demo mode), keep `StorageProvider=supabase`, and keep `DocumentBucketName` blank. Review the change set and ensure only `StagingApi` is modified in place (Replacement=False) before executing.
- After deployment, verify stack `UPDATE_COMPLETE`, check Lambda's running image digest, check environment variable names (never values for secrets), invoke staging health, confirm CloudWatch logs for that invocation, then perform a login-page role-selection test for Employee and Management.
- Lambda IAM execution role and log group `/aws/lambda/ewa-cognito-staging-api` with 7-day retention are in the stack template. The template now explicitly routes Lambda logs to that managed group via `LoggingConfig`; least-privilege delivery and a live correlated invocation/log are still unverified.
- S3 storage cutover remains out of this four-service staging milestone. Keep `StorageProvider=supabase`; no bucket creation required.

### Updated planning estimate (not measured code coverage)
- Cognito source/UI/role path: ~88% implemented; real browser session remains unverified.
- IAM: ~65%; role template/configuration exists; live least-privilege verification remains open.
- Lambda: ~72%; stack/function exists and a prior image build succeeded, but deployed image is stale relative to newest code.
- CloudWatch: ~50%; log group/retention are configured in the template and Lambda emits standard metrics, but a fresh correlated staging invocation has not been verified.
- Four-service end-to-end acceptance: ~25% until the live role-switch/login flow and correlated Lambda log are demonstrated.
- Rough overall four-service completion: ~62–65%, with deployment and E2E evidence as the critical remaining gates.

### Immediate continuation — no unnecessary code work
1. Confirm the latest matching GitHub Actions CI status on final branch head.
2. If green, the user runs the manual workflow at [Build Cognito staging backend image to Amazon ECR](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml), using branch `cognito-staging-integration`.
3. Verify the exact successful image URI/digest in ECR, then create a new CloudFormation change set as specified above.
4. Deploy and test login/role changes and CloudWatch; update the handoff with evidence.
5. Keep PR #3 draft and do not merge or touch Production until staging acceptance tests pass.

---

**Snapshot:** 25 October 2026 (Asia/Kolkata)  
**Repository:** https://github.com/divyanshsaxena2209/enterprise-workplace-assistant  
**Working branch:** cognito-staging-integration  
**Draft PR:** https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3  
**PR base:** aws-service-replacements  
**Latest handoff audit commit:** tracked in the final “Requirements traceability and migration progress” section below; always query the live branch SHA before building/deploying  
**Most recent inspected successful CI checkpoint:** run #40183594878 — https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40183594878 (**115 passed, 10 warnings**; tested source/template SHA `817f9bfc30d62c14b3f6e3ab81b56c180573b1f5`; later handoff update is documentation-only)

Keep PR #3 in draft. The handoff-documentation commit may advance the branch SHA; check the current SHA before any build or deployment. Do not merge into main before real staging end-to-end tests pass.

---

## 1. Project aim and modules

Enterprise Workplace Assistant is a workforce-operations and hiring platform with:
- Employee/management profiles and role-based access control.
- Job listing and publishing, candidate tracking, applications, resume screening, evaluations, recruiter notes and interview workflows.
- Employee onboarding templates, assigned tasks, progress tracking and management oversight.
- Company knowledge-document uploads, retrieval and department-sensitive RAG/chatbot features.
- Separate management and employee dashboards.

The frontend is Next.js App Router. The backend is FastAPI. The relational schema is PostgreSQL accessed through Supabase/PostgREST. Gemini powers LLM features and Qdrant Cloud supplies vector retrieval. Preserve the existing services. The current migration scope is Cognito authentication and IAM/access control only; S3 migration is explicitly out of scope.

## 2. User preferences and non-negotiable guardrails

- Work autonomously where tools permit; stop only when a genuine manual action or unavoidable decision is required.
- Prefer one consolidated high-value test that checks several components/security properties over many repetitive mini-tests.
- Verify current repository, CI, deployment and database state instead of relying on stale summaries.
- For manual steps, provide direct URLs, numbered instructions and exact values.
- Distinguish implemented, tested, deployed and production-cutover status.
- Do not ask for credentials, API keys, passwords, JWT secrets, access tokens, authorization codes, private keys or Supabase service-role keys in chat/screenshots.
- Do not change Production Vercel variables, Production Lambda, Production Supabase schema/data, Production Cognito, or main.
- The user explicitly said the Supabase project named busted must be kept. Never reset, delete, replace or repurpose it.
- The user has no budget / cannot spend money. AWS and Supabase usage may not be $0 even when a resource is small or eligible for a free tier. Do not provision chargeable resources unless the cost is proven acceptable and the user explicitly agrees.
- The user has explicitly decided **not to migrate PostgreSQL to RDS**. Keep Supabase PostgreSQL. Do not create RDS, NAT Gateway, EC2, paid Supabase branches or other cost-prone resources without explicit approval.
- Preserve Gemini and Qdrant Cloud.
- Keep Supabase Storage as-is; do not migrate to S3. Cognito can be enabled only for the isolated staging path after the Cognito end-to-end checks pass. Do not change Production authentication or shared environment variables.

## 3. Production baseline — do not disturb

Last known Production architecture from the previous operational handoff; reconfirm before any future deployment:

| Area | Service |
|---|---|
| Frontend | Vercel: https://enterprise-workplace-assistant.vercel.app |
| Backend | FastAPI container on AWS Lambda |
| Lambda function | enterprise-workplace-assistant-api |
| AWS region | ap-south-1 (Mumbai) |
| Existing Function URL | https://6wdbue2ejwqbs2pqtro4u7ojei0bxrcp.lambda-url.ap-south-1.on.aws/ |
| Container registry | ECR repository enterprise-workplace-assistant-backend |
| Relational database | Supabase PostgreSQL/PostgREST |
| Interactive authentication | Supabase Auth |
| Object storage | Supabase Storage |
| AI | Gemini |
| Vector retrieval | Qdrant Cloud |
| Logging | CloudWatch Logs; final retention/alarms still need review |

A previous smoke test on 21 October showed the live backend health endpoint, legacy login, job listings/details and management candidate views working. The existing Lambda Function URL has AuthType NONE, so application routes must enforce authorization. CORS is not authentication. Pushing an image to ECR does not automatically update the image digest used by Lambda.

**Never point a Cognito signup test at the Production API.** The account-link endpoint can create user/profile records, so use isolated staging services only.

## 4. Current source branch, PR and CI

- Branch: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/tree/cognito-staging-integration
- Draft PR #3, base aws-service-replacements: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3
- Verified code head before this handoff update: b3be0587d1bf910e2fe0086ac1be35266349e46b.
- Latest passing test/frontend-build/backend-test/PostgreSQL-RLS/CloudFormation-lint run for that head: #84 https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39723988185.
- Dedicated Cognito ECR image build #4: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39642644236.
- Staging image tag: cognito-staging-0174c50b992222d01a87bea0f323e9196ddd511d.
- Full image URI: 745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-0174c50b992222d01a87bea0f323e9196ddd511d.
- Code after that backend image build changed SQL migrations, tests, docs and infrastructure rather than backend runtime code according to the PR summary. Check current diff before deploying that image.
- Workflow .github/workflows/build-cognito-staging-ecr.yml runs only by manual dispatch, assumes the separate OIDC role GitHubActions-EWA-Cognito-Staging-ECR and pushes a unique Cognito staging tag. It does not push latest or update Lambda.
- Workflow .github/workflows/test-service-replacements.yml runs frontend build, backend compilation/tests, pre-token handler tests, PostgreSQL RLS/mapping tests and CloudFormation lint for the two checked-in templates.

## 5. Current cloud resources and identifiers

### AWS

- Account: 745531385877
- Region: ap-south-1 (Mumbai)
- Console links: Lambda https://ap-south-1.console.aws.amazon.com/lambda/home?region=ap-south-1 ; Cognito https://ap-south-1.console.aws.amazon.com/cognito/v2/idp/user-pools?region=ap-south-1 ; ECR https://ap-south-1.console.aws.amazon.com/ecr/repositories?region=ap-south-1 ; CloudFormation https://ap-south-1.console.aws.amazon.com/cloudformation/home?region=ap-south-1 ; CloudWatch https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1 ; Billing https://console.aws.amazon.com/billing/home

### Cognito staging pool and pre-token Lambda

- User pool ID: ap-south-1_89s6YRnwQ; region ap-south-1.
- Feature plan shown: Essentials.
- App client: enterprise-workplace-assistant-staging.
- App client ID: 7npkisjjm5jj0fsqf94et8lqra.
- Hosted-login domain observed in the browser: https://ap-south-189s6yrnwq.auth.ap-south-1.amazoncognito.com
- OAuth grant: authorization code. Managed login configuration showed scopes email, openid, and phone; the application flow requests openid email with PKCE. Do not create a browser client secret.
- A new Cognito user was created during the manual test.
- Lambda function: ewa-cognito-staging-pre-token.
- Lambda ARN: arn:aws:lambda:ap-south-1:745531385877:function:ewa-cognito-staging-pre-token.
- The Lambda code has been deployed and its console mock test succeeded. Output included role=authenticated overrides in both the access-token and ID-token generation structures. This is the Supabase infrastructure role, not application MANAGEMENT.
- Cognito Extensions now shows a Pre token generation trigger attached to this Lambda with event version V2_0.

### Result of the manual Cognito browser test

The managed login page opened and the user authenticated. The browser returned to the old CloudFront root, https://d84l1y8p4kdic.cloudfront.net/, and displayed Cognito's generic success page instead of running the Next.js application callback. The URL contained a temporary authorization code; do not reuse or share it.

This test did **not** prove the application's state/nonce/PKCE cookies, callback handler, authorization-code exchange, account-link endpoint, Supabase token acceptance, protected API requests, refresh or logout.

The Cognito client screen showed the CloudFront root as allowed callback, default redirect and sign-out URL. The correct application routes are the Vercel preview origin plus /auth/callback and plus /login. Keep the CloudFront root entry until the correct Vercel routes are added and tested. Remove the old root callback only after successful end-to-end staging login.

Supabase Third-Party Auth for Cognito was created and showed a success toast/enabled state. Some screenshot text rendering of region/pool ID looked odd; the user confirms the entered values match the guide. Do not repeatedly delete and recreate the integration. Its real token acceptance is not yet verified end to end.

### Supabase staging project

- Name: workplace-assistant-staging
- Ref: wxulxcsdpwsyhtpkbazi
- URL: https://wxulxcsdpwsyhtpkbazi.supabase.co
- Region: ap-south-1; status was ACTIVE_HEALTHY when checked.
- The project is newly created and repository migrations were applied to this project only.

### Protected existing Supabase projects

- Production app DB project: workplace-assistant, ref ybkfkdcdhrnjmjvavyhb. Never apply Cognito staging migrations or synthetic data here.
- Protected project: busted, ref zkxpkjgprewurotifgeh, was INACTIVE when checked. User explicitly asked to keep it. Never reset/delete/repurpose it.
- Staging database currently has 0 Supabase Auth users, 0 public profiles, and 0 Cognito identity mappings. The Cognito test user has not yet been linked to a staging application profile.

### Vercel Preview

- Project: enterprise-workplace-assistant, current project ID returned by Vercel connector: prj_ap3BHcwJymfIxo2ABdaBegLJRLBh.
- Latest Ready immutable preview deployment on code head b3be058: https://enterprise-workplace-assistant-qur5zi2pc-divyansh-50b7.vercel.app
- Current branch alias returned by Vercel: https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app
- URLs may change after future pushes. Re-check the current alias and commit before configuring Cognito.
- Vercel environment inventory showed only NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY with shared Production/Preview targets and NEXT_PUBLIC_API_URL with shared Production/Preview targets. No branch-scoped Cognito overrides were found for cognito-staging-integration.
- **Do not set NEXT_PUBLIC_AUTH_PROVIDER=cognito until a separate staging API exists and Preview variables explicitly point to the staging API and Supabase project.** Otherwise Preview may call Production services/data.
- Never edit shared Production/Preview variables to run this test; add branch-scoped Preview values only.

## 6. Code layout and implementation summary

### Frontend

- Next.js source is in frontend/.
- OAuth start route: frontend/app/api/auth/cognito/start/route.ts
- Callback route: frontend/app/auth/callback/route.ts
- Access/refresh route: frontend/app/api/auth/cognito/access-token/route.ts
- Logout route: frontend/app/api/auth/cognito/logout/route.ts
- Token provider: frontend/lib/auth/cognito.ts
- Cognito login component: frontend/components/auth/CognitoLoginPage.tsx
- Cognito flow is opt-in through NEXT_PUBLIC_AUTH_PROVIDER=cognito; otherwise legacy Supabase Auth remains the active path.
- OAuth start creates state, nonce, PKCE verifier/challenge and HttpOnly cookies. The callback verifies returned state, exchanges the authorization code using the PKCE verifier, calls the link/provision API with ID token and nonce, then sets HttpOnly session cookies and redirects to /dashboard.
- Callback validation requires COGNITO_REDIRECT_URI to be the HTTPS route /auth/callback. Using the CloudFront root cannot test that route. A direct hosted-login click also lacks the app-generated state/nonce/PKCE cookies.
- Logout clears session cookies and attempts Cognito token revocation.

### Backend and application roles

- FastAPI lives under backend/.
- Cognito JWT checks: backend/app/core/cognito_security.py. Access token verification uses RS256/JWKS, issuer, expiry, token_use=access, and app client ID. ID-token account-link verification validates signature, issuer, expiry, audience, token_use=id, verified email and the expected OAuth nonce.
- Auth dependencies: backend/app/dependencies/auth.py; identity mapping/resolution: backend/app/services/identity_resolver.py and backend/app/repositories/cognito_identity_repository.py.
- Cognito account-link/provision route: backend/app/routers/auth.py, endpoint /api/v1/auth/cognito/link.
- A one-to-one mapping links Cognito sub to existing public.profiles.id. Application role and account-active state come from the database profile; they are not trusted from browser fields or token application-role claims.
- New public signups are provisioned as EMPLOYEE server-side. The browser cannot self-assign MANAGEMENT.
- COGNITO_ENABLED defaults false. No Production auth cutover has occurred.

### Supabase migration and RLS status

- Migration directory: supabase/migrations/.
- Cognito identity mapping/RLS migration: 20261021000000_cognito_third_party_auth.sql.
- Trigger-function hardening: 20261022000000_harden_trigger_functions.sql.
- Role-scoped RLS/profile/interview protection: 20261022000001_restrict_role_scoped_rls_policies.sql.
- The staging migration registry reported 19 migrations at the last live check. They were applied only to workplace-assistant-staging. Do not blindly replay them and do not run them against Production or busted.
- public.current_profile_id() maps a Cognito subject to a database profile ID. An unmapped Cognito subject resolves to NULL.
- The identity-mapping table has RLS enabled and no client policies; anon/authenticated lack direct SELECT/INSERT permissions. service_role retains backend access.
- Trigger-function hardening pins search_path and revokes direct browser RPC execution for handle_new_user, set_updated_at and log_onboarding_history.
- Role/RLS hardening removes unrestricted public profile reads, scopes broad service-role policies, and revokes direct authenticated table privileges for interviews. Last live SQL audit: 16 of 16 public tables have RLS; 25 public/storage policy expressions use current_profile_id(); zero of those policy expressions use raw auth.uid(); authenticated has no SELECT/INSERT on interviews while service_role retains backend SELECT.
- The Supabase security advisor reports an informational RLS-enabled/no-policy finding for the service-only mapping table, plus SECURITY DEFINER helper-function warnings relevant to RLS. Performance advice includes foreign-key indexes, RLS initplan, unused-index and multiple-policy findings. Do not broadly rewrite unrelated Production policies as part of this migration.
- Staging has no application users/profiles/mappings yet; use only test identities.

### S3 implementation and infrastructure

- Object-storage adapter: backend/app/services/object_storage.py.
- Storage config defaults: STORAGE_PROVIDER=supabase, AWS_REGION=ap-south-1, AWS_S3_BUCKET unset, S3_PRESIGNED_URL_TTL_SECONDS=900.
- Knowledge originals use the knowledge/ prefix. Resume originals use resumes/. Text chunks/embeddings stay in Qdrant; job/application/candidate/profile data remains in Supabase PostgreSQL.
- Current job listings are relational data; the application does not currently implement a job-description attachment upload. Do not claim job PDF attachments have migrated.
- Old Supabase Storage files are not bulk-copied to S3. Existing URLs/objects must continue working for rollback.
- Private bucket template: infra/aws/private-document-storage.yml. It enables all S3 public access blocks, bucket-owner-enforced ownership, SSE-S3 encryption and TLS-only transport.
- No S3 bucket has been created; keep STORAGE_PROVIDER=supabase.
- Cognito staging backend template: infra/aws/cognito-staging-backend.yml. It creates a separate staging Lambda, execution role, CloudWatch log group with 7-day retention and a public HTTPS Function URL. It sets COGNITO_ENABLED=true and STORAGE_PROVIDER=supabase, uses the staging Supabase URL/service-role secret parameter, and allows the Vercel branch origin through CORS.
- That stack is a proposal only. It has not been deployed. Its Function URL is internet-accessible and AWS usage may incur charges. The stack outputs StagingApiFunctionUrl, CognitoLinkApiUrl, PreviewCallbackUrl and PreviewSignOutUrl.
- Do not attach S3 permissions to the Production Lambda or the ECR publisher role. S3 object access belongs on a dedicated staging Lambda execution role and should be limited to knowledge/* and resumes/*.

## 7. What has been tested and what has not

### Verified/passed

1. CI run #84 passed on code head b3be058, including frontend build, backend compile/tests, Cognito pre-token handler tests, PostgreSQL RLS/identity-mapping regression tests and CloudFormation lint.
2. Dedicated staging ECR build #4 passed using GitHub OIDC and the ECR-only staging role.
3. Deployed pre-token Lambda mock event returned Succeeded and output role=authenticated for access and ID token overrides.
4. Cognito managed-login page loaded and a newly created Cognito user authenticated.
5. Supabase staging reported 19 migrations. Live SQL checks confirmed 16/16 public tables have RLS, unmapped Cognito subjects resolve NULL, mapping table is inaccessible directly to browser roles, raw auth.uid() is no longer present in public/storage policy expressions, and direct authenticated interview table access is denied.
6. Supabase staging was ACTIVE_HEALTHY at the last status check.

### Not yet verified

- Real app-originated login/signup starting from the Vercel preview.
- The Next.js /auth/callback route, state/nonce/PKCE verification, code exchange and session cookie creation.
- Real Cognito JWT verification by the staging backend and acceptance by Supabase Third-Party Auth/PostgREST.
- Staging account profile provisioning/link, mapped identity resolution and protected /me endpoint.
- Combined employee/manager authorization denial checks in live staging.
- Refresh/logout path.
- Dedicated staging backend Lambda/Function URL.
- Branch-scoped Cognito preview environment values.
- S3 bucket/policy and live document/resume upload/read/delete.
- Final CloudWatch alerting and production log-retention review.

## 8. Next steps — strict order

### Gate 0: cost and isolation

The user has no budget. Do not deploy a staging Lambda/Function URL/log group stack unless cost has been established as acceptable and the user explicitly agrees to any non-zero exposure. A free-tier label does not guarantee a $0 bill. If a safe zero-cost path cannot be confirmed, continue with local/CI tests and read-only audits; keep Cognito mode disabled.

### Gate 1: isolated staging API (only if Gate 0 permits)

1. Review infra/aws/cognito-staging-backend.yml and the current ECR image tag.
2. CloudFormation in Mumbai: https://ap-south-1.console.aws.amazon.com/cloudformation/home?region=ap-south-1
3. The documented stack name is ewa-cognito-staging-api. The template creates a dedicated staging backend, execution role, 7-day CloudWatch log group and Function URL; it does not reuse or edit Production Lambda.
4. Use only the service-role secret from staging project workplace-assistant-staging in the NoEcho parameter. Never use Production key or share any secret in chat. Staging API settings: https://supabase.com/dashboard/project/wxulxcsdpwsyhtpkbazi/settings/api
5. SupabaseJwtSecret can be blank for Cognito-only tests; legacy Supabase HS256 tokens then fail closed on this staging backend.
6. Review proposed resources/cost before creating. Do not create the stack if charges are unacceptable.
7. After CREATE_COMPLETE, record StagingApiFunctionUrl, CognitoLinkApiUrl, PreviewCallbackUrl and PreviewSignOutUrl outputs. Check health and ensure environment=staging.

### Gate 2: branch-scoped Preview env and OAuth callback

Recheck current Vercel alias before configuring Cognito. At this snapshot it was:
https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app

Only in Vercel Preview scoped to cognito-staging-integration set:

| Variable | Expected value |
|---|---|
| NEXT_PUBLIC_AUTH_PROVIDER | cognito |
| NEXT_PUBLIC_API_URL | StagingApiFunctionUrl only |
| NEXT_PUBLIC_SUPABASE_URL | https://wxulxcsdpwsyhtpkbazi.supabase.co |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | Staging publishable/anon key; never service-role |
| COGNITO_DOMAIN | Exact HTTPS managed-login domain shown in the staging pool |
| COGNITO_APP_CLIENT_ID | 7npkisjjm5jj0fsqf94et8lqra |
| COGNITO_REDIRECT_URI | Current Preview origin plus /auth/callback |
| COGNITO_SIGN_OUT_URI | Current Preview origin plus /login |
| COGNITO_LINK_API_URL | Full staging endpoint ending /api/v1/auth/cognito/link |
| COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS | Match the app client's actual refresh-token lifetime |

Do not alter shared Production/Preview variables or set these in Production. If the alias changes, update callback/sign-out URLs.

In the staging Cognito app client, add the Preview origin plus /auth/callback as Allowed callback and Default redirect URL, and the Preview origin plus /login as Allowed sign-out URL. Keep the old CloudFront root entry until the new flow passes. Authorization code + PKCE, scopes openid/email, and a public client with no browser secret are required.

### Gate 3: one consolidated end-to-end staging test

Once isolated API and Preview configuration are ready, run one comprehensive test from the staging app's /signup or /login. Do not start from Cognito's hosted login directly, because the app must first create state/nonce/PKCE cookies.

Validate together:
1. App-originated login redirects to Cognito and returns to the exact /auth/callback route.
2. Callback validates state/nonce, exchanges code with PKCE, calls the staging link endpoint, sets HttpOnly cookies and redirects to /dashboard.
3. New employee is provisioned/linked only in staging and Cognito subject maps to the correct profile ID.
4. Current-user and an ordinary employee API request succeed with a Cognito access token.
5. A manager-only action is rejected for that employee.
6. Direct browser-role access to interviews and the identity-mapping table is denied by Supabase.
7. Unmapped subject receives no profile/data.
8. Refresh and logout succeed.
9. Legacy Supabase Auth remains selected if the Cognito flag is unset.
10. Confirm Production is unchanged and save CI/preview/API evidence.

Never share the code query URL or token contents. Do not test on Production user data. Keep PR #3 draft until the combined test passes.

### Gate 4: S3 later, only if cost allows

1. Review infra/aws/private-document-storage.yml and its CloudFormation lint.
2. Check cost/free allowance before provisioning; storage, requests and transfer can be billable.
3. If accepted, create one dedicated private staging bucket; preserve all public access blocks, encryption and TLS enforcement.
4. Attach only prefix-restricted PutObject/GetObject/DeleteObject to the staging Lambda role for knowledge/* and resumes/*.
5. Set STORAGE_PROVIDER=s3 only after bucket, policy and staging role are verified.
6. Upload/read/delete a small non-sensitive knowledge file and a test resume; verify presigned URL expiry, object keys/provider metadata and Qdrant ingestion/deletion.
7. Keep Supabase Storage and STORAGE_PROVIDER=supabase for Production/rollback. S3 mode does not copy old objects.

### Gate 5: monitoring and release

- The proposed staging stack sets 7-day log retention; Production log retention/alarms require a separate review.
- Add low-noise Lambda error/throttle/timeout/latency alarms only after checking cost.
- Before Production change, test login, profile/role, jobs, applications, candidates, interviews, onboarding, knowledge/RAG and resumes.
- Keep the PR in draft, review its full diff into aws-service-replacements, and never assume ECR push updates Lambda. Production release is out of scope until staging checks and an approved rollback plan pass.
- No RDS migration.

## 9. Role, data and storage invariants

- MANAGEMENT/HR/ADMIN/EMPLOYEE are application roles from the database profile, not AWS IAM roles.
- Public signup must create EMPLOYEE only; never trust browser-supplied role fields or treat the Cognito infrastructure role claim as MANAGEMENT.
- Cognito sub-to-profile mapping is server-only.
- Lambda uses its execution role for AWS access. Never embed AWS access keys in the app.
- Knowledge documents and resumes remain private and must be served only after application authorization using short-lived presigned URLs.
- Job title/description/requirements remain relational records. Job-description PDF attachments are not implemented.
- Keep Supabase, Gemini, and Qdrant until migration validation is complete.

## 10. Direct links for continuing work

- This handoff: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/docs/README_NEW_CHAT_HANDOFF.md
- Draft PR #3: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3
- Cognito implementation: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/docs/COGNITO_STAGING_IMPLEMENTATION.md
- Staging API deployment guide: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/docs/COGNITO_STAGING_DEPLOYMENT.md
- Private S3 setup guide: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/docs/S3_STAGING_SETUP.md
- Staging Cognito API CloudFormation template: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/infra/aws/cognito-staging-backend.yml
- Private S3 CloudFormation template: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/infra/aws/private-document-storage.yml
- Pre-token handler: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/cognito-staging-integration/infra/cognito/pre-token-generation/index.mjs
- Latest passing CI #84: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39723988185
- Staging ECR build #4: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39642644236
- Staging Supabase: https://supabase.com/dashboard/project/wxulxcsdpwsyhtpkbazi
- Production Supabase: https://supabase.com/dashboard/project/ybkfkdcdhrnjmjvavyhb
- Protected busted project: https://supabase.com/dashboard/project/zkxpkjgprewurotifgeh
- Cognito staging pool: https://ap-south-1.console.aws.amazon.com/cognito/v2/idp/user-pools/ap-south-1_89s6YRnwQ/overview?region=ap-south-1
- Cognito app client: https://ap-south-1.console.aws.amazon.com/cognito/v2/idp/user-pools/ap-south-1_89s6YRnwQ/applications/app-clients?region=ap-south-1
- Supabase Third-Party Auth: https://supabase.com/dashboard/project/wxulxcsdpwsyhtpkbazi/auth/third-party

---

## Starter prompt for the new chat

Read docs/README_NEW_CHAT_HANDOFF.md first. Continue the Enterprise Workplace Assistant AWS migration on cognito-staging-integration and keep PR #3 draft. Verify current branch head, PR, CI, Vercel Preview deployment and env configuration, staging Supabase migrations/RLS, and AWS resource state before acting. Optimize for one consolidated high-value end-to-end test, not repetitive individual tests. The Cognito hosted-login test returned to the CloudFront root and did not exercise the Next.js /auth/callback handler. Do not touch main, Production Vercel variables, Production Lambda, Production Supabase or the protected busted project. Keep Supabase PostgreSQL/Auth/Storage as the default until staging Cognito/S3 tests pass. I have no budget: do not provision potentially chargeable resources unless cost is established as acceptable. No RDS migration; keep Supabase, Gemini and Qdrant.

---

## 11. Milestone update — 2026-10-24 (AWS staging image deployed)

### Completed in this milestone

- GitHub Actions workflow **Build Cognito staging backend image to Amazon ECR #11** succeeded in 7m57s:
  https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39996288700
- Published staging-only backend image tag:
  `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-8222e09e1d8a8f5a7761102b1f0a224f4d9e98ed`
- Updated `infra/aws/cognito-staging-backend.yml` on `cognito-staging-integration` to use that tag. Commit: `bce5d4b1f7b2314707b3b14b74daed207fcf15ba`.
- User applied the updated template to the existing CloudFormation stack `ewa-cognito-staging-api` in `ap-south-1`; console showed stack `UPDATE_COMPLETE` and resource `StagingApi` `UPDATE_COMPLETE`.
- User's Lambda console screenshot confirmed the new image tag and a resolved digest beginning `sha256:25ee90f5120e646f89814227e52dc7798aea742ad5d37406b31906568c759544eb`.
- User confirmed the Lambda environment values `COGNITO_ENABLED=true`, `ENVIRONMENT=staging`, and `STORAGE_PROVIDER=supabase` are correct. Do not request secret values.

### Migration requirements and progress snapshot

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| IAM least-privilege and role-based authorization | **Partially implemented** | A dedicated ECR-only IAM role is used for the image publishing workflow; the staging Lambda has its own execution role. App authorization remains based on database profile roles, with public Cognito signup restricted to EMPLOYEE. Still verify effective deployed policies and end-to-end employee/manager authorization. Do not confuse AWS IAM roles with application roles. |
| Cognito authentication | **Infrastructure deployed; app E2E pending** | Staging pool, app client, pre-token trigger and backend image exist. Previous hosted-login attempt returned to CloudFront root instead of exercising Next.js `/auth/callback`. Next: wire branch-scoped Vercel Preview env and callback allowlists, then one consolidated app-originated login test. |
| Lambda backend | **Staging image deployed; runtime integration pending** | CloudFormation stack and `StagingApi` show `UPDATE_COMPLETE`; new image tag/digest visible in console. Still confirm health/current-user and Cognito link route via the staging endpoint as part of the consolidated E2E test. |
| CloudWatch logging/monitoring | **Basic logging configured; application behavior not verified** | Template configures staging log retention of 7 days. Earlier Lambda test showed `Runtime.Unknown` and log-stream confusion; don't mark logging/runtime healthy solely from stack update. During the consolidated API test, inspect one corresponding CloudWatch log stream and check errors. Alarms remain optional pending cost review. |
| S3 document-storage replacement | **Not implemented/deployed** | `infra/aws/private-document-storage.yml` and `docs/S3_STAGING_SETUP.md` are proposals/guides only. Keep `STORAGE_PROVIDER=supabase` until cost is accepted and private bucket, encryption, public-access block, TLS policy and prefix-scoped role are in place. Then test one non-sensitive knowledge file and one test resume. |
| Supabase PostgreSQL/Auth/Storage, Gemini, Qdrant | **Retained intentionally** | No RDS migration. Keep current defaults and Production untouched until staging migration is proven. Gemini key is configured in staging Lambda per user's report; never print it. |
| Vercel Preview isolation | **Configuration work recorded; verify current live values before relying on it** | Keep Production variables unchanged. Preview must use staging API and staging Supabase, with Cognito provider enabled only for the intended staging Preview. |
| Release readiness | **Not ready** | PR #3 remains draft. Do not merge or cut over Production until one consolidated staging E2E pass, rollback review, and cost review are complete. |

### Initial migration scope (keep this checklist current)

1. **IAM:** least-privilege AWS execution/deployment roles; preserve application authorization by database profile role; never grant role based on browser-supplied claims.
2. **Cognito:** migrate sign-in to Cognito in staging first; app-originated OAuth authorization-code + PKCE callback, identity linking, session refresh/logout and role enforcement must pass.
3. **Lambda:** isolated staging API deployment from the dedicated ECR image; prove the running API works before routing Preview traffic to it.
4. **CloudWatch:** logs with bounded retention, then check real invocation logs/errors; only add alarms after checking costs.
5. **S3:** private staging document storage for knowledge documents and resumes, least-privilege access by `knowledge/*` and `resumes/*`, encryption and TLS enforcement; don't bulk-copy legacy files.
6. **App integration:** branch-scoped Vercel Preview env/callback allowlists only; do not change Production.
7. **Preserve current services:** Supabase PostgreSQL, Gemini and Qdrant stay. Supabase Auth/Storage remain fallback/default until staging Cognito/S3 validation passes. No RDS migration.
8. **Safety/cost:** user has no budget. Do not create additional potentially billable resources or enable extra services/alarms without establishing cost and getting explicit approval.

### Next work — avoid repetitive micro-tests

1. Verify the current staging Preview environment variables and Cognito callback/sign-out allowlists, without changing Production.
2. Connect Preview to the staging API and Cognito.
3. Run **one consolidated end-to-end staging pass** covering app-originated login/callback, state/nonce/PKCE, profile link/provision, employee access, manager-only denial, unmapped-subject denial, refresh/logout, legacy Supabase fallback, and a single correlated CloudWatch log check.
4. After Cognito is sound, review S3 cost and deploy private S3 only with explicit cost approval.
5. Update this handoff at each major milestone with commit/run IDs, what actually changed, evidence, and remaining work. Never label an item complete based only on CI/template validation.

### Handoff maintenance rule

**Required after every major milestone:** update this file on `cognito-staging-integration` with date, changed files/commit or AWS resource, concrete verification evidence, status of IAM/Cognito/S3/Lambda/CloudWatch/Vercel, remaining blockers and the next consolidated action. Keep it factual; distinguish code/CI success from a deployed AWS resource and from end-to-end behavior. Preserve all Production, cost and protected-project constraints. Avoid making the user repeat context or perform many tiny checks.



## Milestone update — 2026-10-24: isolated staging API connected to Preview env

**Branch:** `cognito-staging-integration`  
**Scope:** branch-specific Vercel Preview only; Production untouched.

### Completed with live evidence
- GitHub Actions workflow **Build and push isolated Cognito staging image #11** succeeded in 7m57s. Image tag: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-8222e09e1d8a8f5a7761102b1f0a224f4d9e98ed`. Run: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39996288700
- CloudFormation stack `ewa-cognito-staging-api` is `UPDATE_COMPLETE`. Its Outputs currently report:
  - Staging API base URL: `https://rimxyixnw7r4vgan3stbjiq2aa0tbngm.lambda-url.ap-south-1.on.aws/`
  - Cognito link endpoint: `https://rimxyixnw7r4vgan3stbjiq2aa0tbngm.lambda-url.ap-south-1.on.aws/api/v1/auth/cognito/link`
  - Preview callback: `https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/auth/callback`
  - Preview sign-out: `https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/login`
- Updated Vercel env `NEXT_PUBLIC_API_URL` for Preview branch `cognito-staging-integration` to the staging API URL above. The live env listing confirmed the branch filter and Preview target. This does not change Production.
- Rechecked the branch-scoped Vercel env inventory. Present: `NEXT_PUBLIC_SUPABASE_URL` points to isolated staging project `https://wxulxcsdpwsyhtpkbazi.supabase.co`; `NEXT_PUBLIC_SUPABASE_ANON_KEY` is configured as sensitive; `NEXT_PUBLIC_API_URL` points to staging API. No Cognito frontend variables were present in the branch-specific Preview inventory at this checkpoint.

### Remaining blockers — do not claim end-to-end success
- Cognito frontend Preview variables still need branch-scoped configuration: `NEXT_PUBLIC_AUTH_PROVIDER=cognito`, `COGNITO_DOMAIN`, `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`, `COGNITO_REDIRECT_URI`, `COGNITO_SIGN_OUT_URI`, `COGNITO_LINK_API_URL`, and `COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS`. Confirm the exact active Cognito domain and app-client refresh-token lifetime before setting values. Never configure these for Production.
- Confirm staging Lambda health and account-link route against the deployed image, and correlate one invocation with CloudWatch logs. Stack status alone does not prove runtime health.
- Create a fresh Vercel Preview deployment after env changes, then perform one consolidated app-originated Cognito E2E test. The prior hosted-login-only attempt did not test the app callback/account linking.
- IAM least privilege and role separation remain under review; don't elevate app roles from Cognito claims or browser input.
- S3 replacement is **not deployed**. `STORAGE_PROVIDER=supabase` remains. Review cost and get explicit approval before provisioning S3 or any additional potentially billable resources.
- Preserve Supabase PostgreSQL, Gemini and Qdrant. No RDS migration. Supabase Auth/Storage remain fallback/default until Cognito and S3 staging checks pass. Production Lambda, Production Vercel variables, Production Supabase and protected project `busted` remain off-limits.

### Migration status at this milestone
- **Cognito:** backend trigger and isolated staging pool exist; app callback/E2E pending.
- **Lambda:** isolated staging API deployed/updated; health/runtime verification pending.
- **CloudWatch:** log group retention configured at 7 days; real invocation/error check pending.
- **Vercel Preview isolation:** staging API URL now configured on the target branch; Cognito frontend variables and a fresh deployment pending.
- **S3:** not implemented/deployed; Supabase Storage retained.
- **IAM:** staging execution role exists with scoped log-write actions; complete IAM replacement/least-privilege audit pending.

**Next action:** identify/confirm the exact Cognito managed-login domain and refresh-token lifetime from the staging user pool/app client, then set all Cognito frontend variables for Preview branch `cognito-staging-integration` only. Do not ask the user to run multiple micro-tests; after configuration, do one consolidated verification. Update this handoff again after that milestone.


## Milestone update — 2026-10-24: Cognito domain and token lifetime confirmed

### Verified from the user's AWS console screenshots
- Staging Cognito pool: `ap-south-1_89s6YRnwQ`, region `ap-south-1`.
- Managed-login domain: `https://ap-south-189s6yrnwq.auth.ap-south-1.amazoncognito.com`.
- App client: `enterprise-workplace-assistant-staging`, ID `7npkisjjm5jj0fsqf94et8lqra`.
- Refresh token expiry: **5 days = 432000 seconds**. Access and ID token expiry: 60 minutes each.
- CloudFormation stack `ewa-cognito-staging-api` showed `UPDATE_COMPLETE`; outputs gave the staging API URL and branch Preview callback/sign-out URLs listed in the prior milestone.

### Work attempted and blocker
- Attempted to read the branch-scoped Vercel Preview env inventory and add the seven missing Cognito variables using the connected Vercel integration, scoped to project `prj_ap3BHcwJymfIxo2ABdaBegLJRLBh`, team `team_ajq6NlIYClqTjsKIYbLhLm97`, and branch `cognito-staging-integration`.
- The Vercel API returned `404 Project not found` for both env listing and env creation. **No Vercel environment variables were changed by those failed calls.** Do not claim the Cognito frontend variables have been configured.
- Required values are now known:
  - `NEXT_PUBLIC_AUTH_PROVIDER=cognito`
  - `COGNITO_DOMAIN=https://ap-south-189s6yrnwq.auth.ap-south-1.amazoncognito.com`
  - `COGNITO_APP_CLIENT_ID=7npkisjjm5jj0fsqf94et8lqra`
  - `COGNITO_REDIRECT_URI=https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/auth/callback`
  - `COGNITO_SIGN_OUT_URI=https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app/login`
  - `COGNITO_LINK_API_URL=https://rimxyixnw7r4vgan3stbjiq2aa0tbngm.lambda-url.ap-south-1.on.aws/api/v1/auth/cognito/link`
  - `COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS=432000`
- These must be added only as Vercel **Preview** variables with Git branch `cognito-staging-integration`. Do not edit shared Production variables. Before adding them, resolve Vercel project/team access so the existing project is positively identified and branch scoping is preserved.
- Cognito's app client must also allow the exact callback URL above and sign-out URL above. Do not remove the old CloudFront callback until the app-originated staging flow passes.

### Current status / next consolidated action
- Cognito domain and refresh-token lifetime: **confirmed**.
- Staging Lambda image and CloudFormation update: **deployed**, but end-to-end runtime behavior still pending.
- Vercel branch-scoped Cognito configuration: **blocked by Vercel connector project-not-found response**.
- S3: **not deployed**; keep Supabase Storage.
- IAM: least-privilege review and real role-denial behavior still pending.
- CloudWatch: 7-day retention configured; inspect one correlated invocation during the consolidated staging pass.
- Next: resolve Vercel project access/identifier, add the seven branch-only Preview variables, ensure Cognito callback/sign-out allowlists, create a fresh Preview deployment, then run one consolidated app-originated login/authorization/refresh/logout test. Update this handoff again after the milestone.

---

## 12. Cognito staging sign-in investigation update — 24 October 2026

**Current branch:** `cognito-staging-integration`  
**Latest diagnostic commit:** `b807e5996d71d6f264d5ab0f6d00333cd403c6d1` — `Add safe diagnostics for Cognito staging account-link failures`.

### Observed failure and evidence

- A manual Cognito Preview login reached the application callback but displayed `cognito_account_link_failed`; a subsequent request to the Vercel route `/api/auth/cognito/access-token` returned HTTP 401 with `Your Cognito session has expired. Please sign in again.`
- Code inspection shows the 401 is likely a **secondary symptom**: the callback only sets the session cookies after the staging backend account-link endpoint succeeds. When linking fails, it clears the temporary OAuth cookies and redirects to login, leaving no application access/refresh cookies.
- The callback POSTs to `COGNITO_LINK_API_URL` (expected staging Lambda Function URL path `/api/v1/auth/cognito/link`) with the Cognito ID token, OAuth nonce, and optional signup profile.
- The callback intentionally hides backend response bodies from the browser. Before this update, it also emitted no diagnostic for a non-2xx link response or a fetch exception.
- CloudWatch Logs Insights on 24 October searched the last seven days across four log groups. Staging API invocations on 23 October included a 26.75-second request at 20:18:24 UTC and shorter requests around 20:21 and 20:32 UTC, but the visible log rows did not expose the HTTP response or application exception. An older 22 October startup failure showed Google `DefaultCredentialsError`; this is historical evidence and not proven to be the current account-link failure.
- The staging API log stream showed Python/Starlette warnings. These warnings alone do not establish the account-link root cause.

### Code change just made

- Updated `frontend/app/auth/callback/route.ts` to log only the staging account-link HTTP status for non-success responses, or the exception class for fetch/parsing failures.
- This deliberately does **not** log ID tokens, nonce, signup profile, response bodies, or other user data.
- Commit: `b807e5996d71d6f264d5ab0f6d00333cd403c6d1`.
- The change is committed on the staging branch only. It does not change Production, Cognito, Lambda configuration, Supabase schema/data, or role logic.
- CI and a new Vercel Preview deployment must be confirmed before the next attempt. Do not assume this diagnostic commit is deployed until the Vercel Preview shows the matching commit and Ready status.

### Next high-value action

1. Confirm the GitHub CI run for commit `b807e5996d71d6f264d5ab0f6d00333cd403c6d1` passes and the corresponding Vercel Preview deployment is Ready.
2. Make one new sign-in attempt using the existing staging Cognito test user (do not create more accounts).
3. Inspect Vercel Runtime Logs for `[cognito-staging] account-link endpoint returned a non-success status` or `[cognito-staging] account-link request failed before a successful response`. Use the logged status or exception class to select the actual fix. Do not treat the downstream `/api/auth/cognito/access-token` 401 as the root cause unless new evidence supports that.
4. If status is 404, inspect whether the verified Cognito email has an existing profile or the signup profile cookie was provided. If 401/403, investigate ID-token verification/configuration; if 409/500, investigate Supabase staging user/profile/mapping provisioning; if no response/exception class is logged, investigate endpoint URL/network/CORS and Lambda invocation. These are decision branches, not confirmed diagnoses.
5. Keep PR #3 draft. Do not touch Production, `main`, the protected `busted` project, or provision additional resources. Preserve Supabase Auth/Storage as fallback until the full staging flow passes.

### Migration status snapshot

- **Implemented:** Cognito staging pool/app client, pre-token trigger, isolated staging API/Lambda Function URL, branch-scoped Vercel environment setup, callback/token routes, Cognito identity-link endpoint, IAM role-based authorization groundwork and CloudWatch log groups.
- **Partially validated:** staging image build and deployment, Cognito hosted sign-in, pre-token mock test, CI/build checks and Lambda invocations.
- **Not yet end-to-end verified:** successful callback/token exchange, profile provisioning/linking, Cognito-to-Supabase token acceptance, employee/manager authorization checks, refresh/logout, legacy Supabase-auth fallback after Cognito opt-in, S3 private storage replacement and production cutover.
- **S3:** still not migrated; Supabase Storage remains the active/default provider. Do not deploy S3 resources without explicit cost approval.
- **IAM:** dedicated staging execution/OIDC roles and least-privilege groundwork exist; final policy audit and end-to-end role checks remain.
- **CloudWatch:** log groups are present and basic Lambda events are visible; useful application-level account-link diagnostics were missing and are now being added.

---

## 13. Cognito account-link diagnostic update — 24 October 2026

**Working branch:** cognito-staging-integration  
**Relevant source files:** frontend/app/auth/callback/route.ts; frontend/components/auth/CognitoLoginPage.tsx; frontend/app/api/auth/cognito/access-token/route.ts

### Findings from the latest investigation

- The user-visible failure is cognito_account_link_failed; a separate Vercel Request Logs entry showed GET /api/auth/cognito/access-token returning HTTP 401. The access-token 401 can be expected after callback failure clears session cookies; it is not proof of the original cause.
- Read-only SQL against staging only (wxulxcsdpwsyhtpkbazi) returned 0 rows in auth.users, public.profiles, and public.cognito_identity_mappings. Therefore this staging test has not successfully provisioned and mapped an app user.
- Historical CloudWatch rows included an initial slow/cold Lambda invocation and older runtime warnings. Those are not enough to identify the link endpoint's actual HTTP status/error code.
- No Cognito tokens, authorization codes, user profile values or keys were read or logged in this investigation.
- Vercel Hobby runtime log retention is limited to one hour, so the previous attempt's exact callback log may no longer be available. Vercel connector reads for this project were returning project-not-found/forbidden; deployment state was not independently verified through that connector.

### Code changes committed in the staging branch

1. Commit b807e5996d71d6f264d5ab0f6d00333cd403c6d1: add safe logging of the link endpoint HTTP status, or the exception class for a fetch failure.
2. Commit d28d342607b52164c06b32c972b4ec8379e83174: parse only an allow-listed error_code from the staging backend's standardized error response and log status + safe errorCode; never log response bodies, tokens, nonce or user data. Translate common backend error categories into diagnostic login error keys.
3. Commit 5b4cd788f826f9ba4c53db380a458fca9c57ab83: add corresponding user-safe explanations for token rejection, profile identity mismatch, mapping conflict, invalid profile data, database error, unavailable service, and generic backend failure.

The new behavior is frontend-only and does not modify AWS resources, the staging Supabase database, Production environment variables, Production Lambda, or the main branch. It is not considered deployed until the Vercel Preview is Ready on a commit containing these changes.

### Next action after Preview is Ready

- Make one app-originated attempt through the current branch Preview, using /signup to supply the employee profile and the existing test Cognito user if the Hosted UI allows sign-in from that screen. Do not begin at the Cognito dashboard/root URL. If the existing Cognito identity cannot complete the signup path, stop and report the exact on-screen message rather than creating multiple identities.
- The login page should now show a more specific safe category. That single result should tell us whether the failure is token/JWKS validation (cognito_link_token_rejected), identity mismatch (cognito_link_identity_mismatch), conflict, validation, database, service or generic backend.
- If a generic failure remains, use the newly logged Vercel entry to record the safe HTTP status/error code and correlate with the same staging Lambda invocation in CloudWatch. Do not run broad repetitive log queries.
- Do not change the Cognito refresh-token lifetime based only on Vercel's Needs Attention warning. It is a configuration-exposure warning for a numeric value, not evidence of this profile-link failure.
- Keep PR #3 draft. Do not deploy a new backend image or alter CloudFormation unless the diagnosis shows it is necessary and the user accepts any possible cost. Keep Supabase Auth/Storage as fallback and do not perform a Production cutover.

---

## 14. Backend provisioning error classification fix — 24 October 2026

### Root defect identified in source

Review of `backend/app/routers/auth.py` found that failures from `client.auth.admin.create_user(...)` were caught, followed by one profile lookup. If that lookup returned no profile, the backend raised `ConflictError` (HTTP 409) for every exception, including Auth API/configuration failures, trigger/database failures, or transient service failures. This falsely labeled provisioning failures as account conflicts and obscured the original cause. The Supabase staging database currently has 0 Auth users, 0 profiles, and 0 Cognito mappings, so successful provisioning has not occurred.

### Code fix committed on `cognito-staging-integration`

- `713a63c35fd143cb5e0ed8ca92dc7144611480ad`: change failed shadow-user provisioning without a profile into `DatabaseError` instead of `ConflictError` and log only exception class (no email, tokens, or exception text).
- `153529a28098bd9f8f7d83e399e3091764f4cccd`: add `backend/tests/test_cognito_provisioning_errors.py`, a regression test that verifies an Auth admin creation failure without a profile is not mislabeled as a conflict.
- `20c2009140cab30179a4f03923d12b56432e1f00`: include the new regression test in the isolated service-replacement CI suite.
- `b5c745afcbf587dc180b7307b57b8d570b66800f`: log only the upstream numeric HTTP status (when present) alongside exception class, to aid diagnosis without logging user data, response text, credentials, tokens, or email.
- `b472156059f51bb79bbf900722e586968d66f6ad`: change the frontend message for `CONFLICT` to a neutral warning because the currently deployed backend may still emit this legacy code for a provisioning failure.

The broader staging callback diagnostics remain in place: frontend logs an allow-listed backend error code and HTTP status, and shows targeted messages for authentication, identity mismatch, conflict, validation, database, service-unavailable, and backend-error categories. The account-link failure still is **not considered fixed in the live environment** until the new backend image is built/deployed and the complete sign-in succeeds.

### Validation / deployment gates

- Previous service-replacement CI run `40084027344` passed frontend build, Python compilation, CloudFormation lint and isolated tests for the frontend-only diagnostic commits.
- CI run `40084393987` completed **success** after the backend provisioning fix. It passed frontend build, backend/test compilation, CloudFormation template validation and the isolated service replacement tests; the test logs report `54 passed, 10 warnings` (warnings are recorded in the run and are not test failures).
- Vercel's check status for the latest handoff source previously showed success; Vercel connector read APIs have returned not-found/forbidden, so deployment details must be confirmed from the GitHub Vercel status and/or user dashboard if necessary.
- The running staging Lambda still uses its existing ECR image, which does not include the new backend source changes. To apply the backend fix, a new staging backend image must be built/pushed to ECR and the staging Lambda/CloudFormation stack updated. This can cause ECR storage/build costs. Because the user has no budget, do not trigger that build/deployment without explicit acceptance of any nonzero cost. Do not touch Production, `main`, Production Supabase, or `busted`.

### Next action

1. Confirm the current CI run passed; do not start another redundant test suite.
2. Before a new staging Lambda image can be deployed, the user must explicitly confirm whether any nonzero ECR/AWS cost is acceptable. If not, keep the backend fix committed but undeployed; do not pretend the live API uses it.
3. If cost is approved and the image is deployed, do one app-originated `/signup` staging run and inspect the specific displayed error category plus the corresponding sanitized CloudWatch event. Avoid extra accounts and broad repeated queries.
4. Keep PR #3 draft until full staging end-to-end validation and rollback requirements pass.

---

## 15. CI validation checkpoint — 24 October 2026

- GitHub Actions run `40084393987` completed **success** on code commit `b5c745afcbf587dc180b7307b57b8d570b66800f`: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40084393987
- This single workflow run passed the Cognito pre-token test, frontend dependency install/build, backend and test compile, CloudFormation lint, and the isolated service replacement tests including the new `test_cognito_provisioning_errors.py` regression test.
- GitHub's Vercel status for the code commit `b5c745afcbf587dc180b7307b57b8d570b66800f` reported success at https://vercel.com/divyansh-50b7/enterprise-workplace-assistant/CpwfB4wD7SbHLo2TUxfP6sHDG49i. The current branch tip at the time of this note is a subsequent handoff-only commit and its Vercel status was still pending; verify the branch alias points to a Ready deployment before the next sign-in.
- The repo source fix is validated by CI, but the live AWS staging Lambda still uses the previous container image. Applying the backend fix requires a new ECR image plus Lambda image update. Do not do that until the user explicitly accepts any nonzero ECR/AWS costs. No Production service or staging database was modified during this code work.

---

## 16. Staging backend image build milestone — 24 October 2026

- GitHub Actions build workflow run **#12 succeeded** on commit `d0d33cb4b4ac379e6bdd32378de817f7560c5dfe` (7/7 minutes? recorded total run duration 2m47s): https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40084892406
- The Docker build logs confirm the image was pushed to ECR with tag:
  `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-d0d33cb4b4ac379e6bdd32378de817f7560c5dfe`
- Exact single-platform linux/amd64 image digest from the successful push:
  `sha256:fb2fe145a2821db094a0886927a7e80a2e617fb535ff61e7769bd8ba19039698`
- Use immutable image URI for the staging Lambda code update (not an older tag):
  `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend@sha256:fb2fe145a2821db094a0886927a7e80a2e617fb535ff61e7769bd8ba19039698`
- Verified at that exact source commit: `backend/app/routers/auth.py` contains the new safe failure-classification/logging behavior, and `backend/tests/test_cognito_provisioning_errors.py` contains the regression test.
- **Not yet deployed:** existing staging Lambda still runs the prior resolved digest until its code is explicitly updated. Next step is update only function `ewa-cognito-staging-api-StagingApi-xlm7Nj337FcE` using the immutable URI above, preserving its existing environment/config and permissions. Do not change the CloudFormation stack parameters or any Production Lambda/config. After image update completes, inspect sanitized logs and do one app-originated staging signup flow. If the backend returns a more specific error, diagnose that rather than repeating generic queries.
- Cost note: ECR image push/in-region ECR-to-Lambda transfer has no ingress/transfer charge; private image storage is billed over time. Image size shown by the build output is not the billed storage amount, and the user's remaining credits/eligibility cannot be independently verified here. Preserve all existing tags for rollback; do not delete old ECR images as part of this deployment.

---

## 17. Staging Lambda image alignment / E2E gate — 24 October 2026

- Expected backend image digest: `sha256:fb2fe145a2821db094a0886927a7e80a2e617fb535ff61e7769bd8ba19039698`, built in GitHub Actions run `40084892406` from the corrected staging code. The user supplied the same full image URI from the AWS console, so proceed on the assumption the Lambda's **Resolved Image URI** now matches; do not call it fully validated until successful sign-in/profile linking proves the running path.
- Current staging branch head at the checkpoint: `a156aae4caa5cb4aeb6c34451240417b33ddfb04`. GitHub reports the Vercel Preview status success for this head: https://vercel.com/divyansh-50b7/enterprise-workplace-assistant/3JMQD4FNpt4woQrj9f9ASG6uL3Y3. Connected Vercel deployment/log detail reads are denied (403/404), so do not claim to have independently inspected private Vercel runtime logs.
- Confirmed source behavior: `frontend/app/signup/page.tsx` selects `CognitoSignupForm` when `NEXT_PUBLIC_AUTH_PROVIDER=cognito`; the form POSTs `{ profile: { full_name, department, job_title, ... } }` to `/api/auth/cognito/start`, which stores the profile and creates OAuth state/nonce/PKCE cookies before redirecting to Cognito. `/auth/callback` exchanges the code, POSTs the ID token + nonce + pending profile to the staging `COGNITO_LINK_API_URL`, and only sets the app token cookies after a successful link response.
- **Single required end-to-end check:** use the configured branch alias (it matches Cognito's allowed callback URI), open `/signup`, provide a test employee name/department/job title, and continue to Cognito. Use the **existing Cognito test account** if it already exists; do not create additional Cognito users. Complete the hosted UI sign-up/sign-in, then observe whether the app lands on `/dashboard` or shows a specific `cognito_link_*` message. Do not use an ephemeral deployment hostname; callback cookies are scoped to the browser host and Cognito redirect URI must match the branch alias.
- After the one flow, run one read-only staging database check for counts in `auth.users`, `public.profiles`, and `public.cognito_identity_mappings`; expected to become 1+ consistent records after successful first provisioning. If the flow fails, the new callback will log only the HTTP status + allow-listed error code (or exception class). Do not ask user for further broad CloudWatch queries; use exact timestamp/diagnostic category to follow up.
- Verified baseline before testing: staging project `wxulxcsdpwsyhtpkbazi` had 0 auth users, 0 profiles, and 0 Cognito mappings. Production and protected `busted` remain untouched. PR #3 remains draft. S3 Storage replacement is still not deployed; Supabase Storage remains active/default.

---

## 18. First post-deployment Cognito signup result — 24 October 2026

- After the user reported the Lambda Resolved Image URI matches the fixed digest `sha256:fb2fe145a2821db094a0886927a7e80a2e617fb535ff61e7769bd8ba19039698`, one staging `/signup` flow reached the new frontend error category `cognito_link_database_error`.
- The screen message is: `The staging API could not save the employee profile. The staging database/API configuration needs repair; retrying signup is unlikely to help.` This category is emitted by the backend when `client.auth.admin.create_user(...)` throws and the follow-up lookup still finds no `public.profiles` record. It is not proof of a PostgreSQL write failure specifically: the wrapped exception may originate from Supabase Auth credentials/authorization, request validation, Auth service, or the `on_auth_user_created` trigger.
- Read-only query against staging `wxulxcsdpwsyhtpkbazi` after the failed flow shows `auth.users=0`, `public.profiles=0`, `public.cognito_identity_mappings=0`. Therefore provisioning did not commit.
- Read-only inspection shows `auth.users` has an `on_auth_user_created` trigger invoking `public.handle_new_user()`. The current function inserts profile columns that exist in the staging `public.profiles` schema (`id`, `email`, `full_name`, `role`, `employee_id`, `department`, `job_title`, `phone`, `location`, `bio`, `avatar_url`, `is_management_verified`, `is_active`). The observed schema has no profile role CHECK constraint that would reject `EMPLOYEE`, so do not change schema or role values speculatively.
- The latest staging image includes a safe warning line from the `create_user` exception handler: `Cognito staging shadow-user provisioning failed (exception_type=<class> upstream_status=<numeric status or None>)`. It logs only exception class and validated numeric upstream HTTP status, not response bodies, email, token, or credentials.
- **Next required evidence:** inspect the latest `/aws/lambda/ewa-cognito-staging-api-StagingApi-xlm7Nj337FcE` log event for that exact warning at the timestamp of this failed attempt. Use its `exception_type` and `upstream_status` to branch diagnosis: 401/403 likely service-role credential/authorization; 4xx likely request/provider validation or user state; 5xx or status missing likely Auth service/database trigger/transient connection. These are diagnostic directions, not confirmed causes. No need to rerun signup or execute another broad CloudWatch query.
- No Production settings/data were modified. Do not use Supabase SQL to insert/repair a user manually. Keep PR #3 draft and update this handoff after the root cause and final successful flow are confirmed.

---

## 19. Staging profile GRANT fix — 24 October 2026

**Root cause confirmed:** Supabase staging project `wxulxcsdpwsyhtpkbazi` logged HTTP 403 / PostgREST error 42501 for the backend's `GET /rest/v1/profiles` request during Cognito signup. The request JWT role was `service_role`. Catalog checks showed `service_role` had no SELECT, INSERT or UPDATE table privileges on `public.profiles`, even though the role-scoped service-role INSERT policy existed. RLS policies do not replace PostgreSQL GRANT privileges.

**Fix applied to staging:** applied migration `grant_service_role_profile_privileges` with `GRANT SELECT, INSERT, UPDATE ON TABLE public.profiles TO service_role;`. This succeeded on staging only. Follow-up query confirms those three privileges are now true; DELETE remains false, and direct SELECT for anon/authenticated remains false. No rows were inserted or changed.

**Repository commits:**
- `5200da8497cee2719ac03ad772cebca7b1abfb27`: adds `supabase/migrations/20261024000000_grant_service_role_profile_privileges.sql`.
- `6c41a352adc5f3d62c74ed90fdbcdde90ebb3cbc`: regression assertion in `backend/tests/test_cognito_rls_migration.py` that checks backend role privileges and browser-role denial.

**Next:** wait for CI on branch head `6c41a352adc5f3d62c74ed90fdbcdde90ebb3cbc`; then do one end-to-end staging signup/login. Verify staging counts for auth users, profiles and Cognito mappings, and dashboard success. Do not run more broad log queries. Production, `main`, and protected `busted` were not modified. S3 replacement has not started; Supabase Storage remains active. PR #3 stays draft until end-to-end auth and authorization checks pass.


## Follow-up update — 2026-10-24 (staging-only profile/jobs corrections)

- Confirmed staging Supabase project `wxulxcsdpwsyhtpkbazi` is the target; Production and the protected `busted` project remain untouched.
- The existing staging profile grants migration is `20261024000000_grant_service_role_profile_privileges.sql`.
- Applied staging-only `GRANT SELECT ON public.jobs TO service_role` after the staging `/jobs` request explicitly returned PostgreSQL `42501`. No browser role was granted direct table access.
- Next source migrations added in `cognito-staging-integration`:
  - `20261024010000_grant_service_role_jobs_select.sql`: mirrors the narrow staging grant for repeatable environments.
  - `20261024020000_auto_assign_employee_ids.sql`: generates employee IDs for newly created profiles and backfills existing profiles whose ID is blank, without changing profile roles or overwriting nonblank IDs. Employee roles receive `EMP-######`; management roles receive `MGR-######`.
- `TopNavbar.tsx` now uses the same Dicebear `7.x/adventurer` fallback as the profile page, because the profile page is where the user confirmed the cartoon avatar already renders.
- The Cognito public signup flow intentionally remains employee-only. Management role assignment must continue to come from a trusted administrative workflow, never a public signup dropdown.
- Added test coverage for the grants and employee-ID trigger. CI must be checked before the staging database receives the employee-ID migration. After CI passes, apply that migration to staging and verify the newly signed-up profile is assigned an ID. Do not merge the draft PR until the live Cognito staging flow is verified.
- Existing production/legacy Supabase profiles must not be bulk-copied or recreated. They continue to belong to the existing profile/auth rows; any Cognito identity should be linked by verified email and the existing identity-mapping route, preserving that profile's role and data.


## Follow-up update — 2026-10-24 (signup role hardening)

- CI run 106 for commit `b0aa75b19ec5a0db23c10af90581639d2f48a916` passed, including the frontend build and isolated service-replacement test.
- The staging-only `20261024020000_auto_assign_employee_ids.sql` migration was applied successfully to project `wxulxcsdpwsyhtpkbazi`. The existing staging profile is now `EMPLOYEE` with generated ID `EMP-000001`; all staging profiles have a nonblank ID.
- `/jobs` now has the missing service-role SELECT grant in staging. `anon` and `authenticated` still cannot directly SELECT from `public.jobs`; the API service layer continues to force Employee results to Published jobs.
- A public-signup role escalation path was found in the legacy Supabase `handle_new_user` trigger. A follow-up migration `20261024030000_harden_public_signup_roles.sql` now takes the role only from trusted `raw_app_meta_data` (Management if explicitly admin-assigned; otherwise Employee), ignores public `raw_user_meta_data.role` and `raw_user_meta_data.employee_id`, and retains the secure employee-ID generator. The legacy signup UI also labels Management as administrator-assigned and removes the manual employee-ID input. The Cognito signup UI now visibly presents Employee self-service versus administrator-assigned Management.
- Regression tests exercise spoofed public metadata and trusted app-metadata provisioning. GitHub Actions run 107 for commit `6fd033077817b6e43826594774a704f78bacca57` **passed**: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40106803383. Vercel reported the Preview deployment as completed for the same source commit: https://vercel.com/divyansh-50b7/enterprise-workplace-assistant/DkQSuCrn4oSDPf8sBYiXXC7Kg779.
- After CI passed, migration `20261024030000_harden_public_signup_roles.sql` was applied to staging project `wxulxcsdpwsyhtpkbazi`. Read-only verification confirmed one staging profile, role `EMPLOYEE`, ID `EMP-000001`, active=true, and is_management_verified=false. No profile IDs are blank.
- Post-migration grants: service_role has SELECT/INSERT/UPDATE on profiles but not DELETE; service_role has SELECT on jobs only; anon/authenticated cannot SELECT either table. `handle_new_user()` is SECURITY DEFINER with fixed `search_path=pg_catalog, public, auth, pg_temp`; direct EXECUTE is denied to anon/authenticated. Do not change Production or merge the draft PR until the staging UI/E2E flow is manually verified.


## Follow-up update — 2026-10-24 (complete backend table grants and profile edit route)

- Staging audit found that while `/jobs` was fixed, `service_role` still lacked SQL privileges for applications, candidates, resumes, candidate scores, application status history, and recruiter notes. These are all accessed by trusted FastAPI repositories, and the old frontend silently swallowed employee application-list errors.
- Least-privilege migration `20261024040000_grant_backend_service_role_table_privileges.sql` was added, CI run 108 for code commit `f7929fd383e5bcc7098bfb8ba216d635e29c5c1c` passed (https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40107673040), and the migration was applied to staging project `wxulxcsdpwsyhtpkbazi`. Read-only catalog checks confirmed the exact service-role privilege matrix: jobs/applications/candidates SELECT+INSERT+UPDATE; resumes SELECT+INSERT; candidate_scores SELECT+INSERT+UPDATE; application_status_history SELECT+INSERT; recruiter_notes SELECT+INSERT+UPDATE+DELETE. No hard DELETE is granted to jobs, applications, candidates, resumes, candidate_scores, or application_status_history. For all seven tables, both `anon` and `authenticated` have no direct SELECT, INSERT, UPDATE, or DELETE privileges.
- The Profile page edit path has been moved from direct browser Supabase table writes to authenticated `PATCH /api/v1/profile` through `fetchWithAuth`. It uses the same Cognito identity resolver and trusted service-role repository as profile reads; the request schema does not permit changing role, employee ID, or email. Empty phone values are normalized to `null`.
- Do not merge PR #3; live E2E testing remains required before migration completion.


## Existing-profile access clarification — 2026-10-24

The Cognito staging environment uses its own Supabase project (`wxulxcsdpwsyhtpkbazi`) and does **not** contain the Production profile dataset. Its only current profile is the staging test employee with ID `EMP-000001`. Do not tell existing Production users to sign up through the staging preview yet: if their profile row has not been migrated into the staging project, the staging callback cannot link to that Production-only row and may create a separate staging test profile.

For now, existing users should continue signing in through the current Production application and its currently configured auth flow. The verified-email identity-link route links a Cognito subject only to a matching profile and Auth identity **inside the same Supabase project**; the route does not reach across environments. Existing profiles must be moved to Cognito only through a separately planned, reviewed Production migration that preserves profile IDs, existing roles, profile data, and verified email matching. No Production records were changed during this work.

## E2E status and required final verification — 2026-10-24

- GitHub Actions run 108 passed for code commit `f7929fd383e5bcc7098bfb8ba216d635e29c5c1c`. Vercel reported Preview deployment complete for that source commit at https://vercel.com/divyansh-50b7/enterprise-workplace-assistant/5eAh8DeBmrmyTsgrheahgTNGTkKF. Follow-on commits `28ba760137645d69a2efdad5c92808dca3accd59` and the subsequent handoff updates are documentation-only; the tested functional code is still commit `f7929fd383e5bcc7098bfb8ba216d635e29c5c1c`.
- Staging database role-spoof probe passed: public `raw_user_meta_data` attempting `role=MANAGEMENT`, a spoofed employee ID, and `is_management_verified=true` resulted in EMPLOYEE plus generated EMP ID and false verification; trusted `raw_app_meta_data` management assignment resulted in MANAGEMENT plus generated MGR ID. Temporary test records were deleted.
- Full table privilege checks passed after migration 0400. The profile remained active EMPLOYEE with `EMP-000001`; no staging profile lacks an ID.
- The Vercel connector did not authorize direct fetch of this team's protected preview, so the page itself has not been visually E2E-tested from this session. Do not merge PR #3 until the user manually verifies Cognito signup/login and the role/ID/avatar/jobs/profile-edit behavior on the preview deployment. Keep Production and `busted` untouched.


## Handoff correction — 2026-10-24 (final privilege audit)

- Verified directly against staging after migration 0400: every expected service_role grant matches the repository-operation matrix, and all four table privileges (SELECT/INSERT/UPDATE/DELETE) are false for both browser-facing roles on jobs, applications, candidates, resumes, candidate_scores, application_status_history, and recruiter_notes. Profiles remain backend-only; service_role has SELECT/INSERT/UPDATE but not DELETE, and authenticated has no UPDATE grant on profiles.
- The actual GitHub Actions run number is **108** (not 110): run ID `40107673040`, successful for code commit `f7929fd383e5bcc7098bfb8ba216d635e29c5c1c`. The later commits `28ba760137645d69a2efdad5c92808dca3accd59`, `792eaa571eec9c06ebcb2fb72244efb7843f5be3`, and the current handoff-correction commit are documentation-only; the tested functional code remains `f7929fd383e5bcc7098bfb8ba216d635e29c5c1c`.
- Staging data remains unchanged by the grants migration: exactly one profile, `EMPLOYEE / EMP-000001`, active, not management-verified, and no profile lacking an employee ID. The signup role-hardening migration is present in the active trigger definition.
- **Do not call end-to-end complete yet.** The Vercel status is successful, but direct preview inspection from this session returned HTTP 403 from the Vercel connection; visual and interactive browser testing still needs the user. Keep PR #3 open and draft.
- A source audit found `frontend/components/dashboard/ManagementDashboard.tsx` and `frontend/components/onboarding/ManagementOnboardingDashboard.tsx` still query backend-only Supabase tables/profiles directly from the browser. Those screens need management-protected API endpoints before management dashboard/onboarding can be declared Cognito-compatible. Do not grant browser access to those tables as a workaround.
- When resuming, start by converting those two Management UI data paths to protected backend endpoints (or record the scope decision), run CI, then have the user verify the preview: employee avatar/name, generated ID, profile edits, published-only Jobs results, employee/management denial boundaries, and Management routes under a trusted Management account. Do not merge PR #3 before those checks; do not modify Production or protected project `busted`.


## Continuation update — 24 October 2026 (employee-ID CI regression)

**Active branch and PR**
- Repository: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant
- Continue on `cognito-staging-integration`; PR #3 remains **open and draft** against `aws-service-replacements`.
- Latest code commits in this continuation:
  - `38086e305f78a86c8d9c92feae761f973e4577c2`: restored the management-only employee-ID endpoint and schema in `backend/app/routers/profile.py`.
  - `2681bdcbe75a8d4b19189d9d497dae47306145d7`: cleaned up imports for that endpoint.
- CI runs for those commits were queued/in progress at the time this note was written:
  - https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40108589567
  - https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40108599409
  Re-check both runs before relying on this change as tested.

**Why this code follow-up was necessary**
- The previous run, https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40108374461 (head `53585e9bed348c4d1674b88e4e7db9b6a16e4201`), failed the service-replacement test step after the frontend build, backend compile and CloudFormation lint succeeded. Result: **46 passed, 8 failed**. All 8 failures were in `backend/tests/test_profile_employee_id.py`: the test contract expected `ProfileRepository`, `EmployeeIdUpdateRequest`, and `assign_employee_id` in `backend/app/routers/profile.py`, but the route had disappeared from that module.
- The route is now restored as `PATCH /api/v1/profile/employees/{profile_id}/employee-id`, guarded with `require_management`. It accepts only `SS-12345` format, returns 404 when the target profile is missing, rejects non-EMPLOYEE targets, and writes only the `employee_id` field through `ProfileRepository`. Database-generated `EMP-######` / `MGR-######` assignment remains the signup default. This endpoint does not grant/alter roles.
- The new commits require a fresh CI result; this tool session cannot run the repository tests locally. Do not describe the CI as passing until one of the new runs completes successfully.

**Correction to the prior source-audit note**
- The earlier note saying management dashboard components still read Supabase backend-only tables directly is stale for the current branch. Source inspection confirms `frontend/components/dashboard/ManagementDashboard.tsx` calls `/dashboard/management-summary`, backed by `backend/app/routers/dashboard.py` with `require_management`.
- `frontend/components/onboarding/ManagementOnboardingDashboard.tsx` calls `/onboarding/management/progress`, backed by `backend/app/routers/onboarding_portal.py` with management authorization. Do not add browser-facing table grants to fix either screen.
- These source checks do **not** replace a live browser/Preview test. The Vercel deployment could not be inspected from the connector (403); visual and interactive checks remain unverified.

**Migration status / next gates**
1. Re-check CI for the two commits above; fix any actual remaining test failures and keep PR #3 in draft.
2. The staging backend image / Cognito flow must be checked against the live staging Lambda and its resolved immutable ECR image before testing. The handoff's prior runtime note describes a `cognito_link_database_error` with zero staged `auth.users`, `profiles`, and Cognito mappings. A later note says missing staging `service_role` SQL grants were corrected; do not repeat signup blindly. Use the specific sanitized Lambda warning and read-only privilege/migration checks to confirm the present state.
3. Do not create resources simply to advance the flow: the user has no budget and the staging CloudFormation Lambda/Function URL, S3, ECR storage, logs and transfer can incur charges. No new chargeable AWS resource should be created without a confirmed acceptable cost and explicit approval.
4. Keep `COGNITO_ENABLED` opt-in and `STORAGE_PROVIDER=supabase` as defaults. No production cutover, main-branch change, RDS migration, or changes to the protected `busted` project.
5. Consolidated live staging E2E is still outstanding: begin sign-in from the actual branch preview `/signup` route (so state/nonce/PKCE cookies are made), confirm callback and profile mapping/provisioning, verify employee-vs-management denial boundaries, test profile edit/employee ID, published-only jobs, dashboard/onboarding routes, refresh/logout and legacy Supabase behavior. Do not use Production credentials/data or create more test identities without need.


## CI result follow-up — 24 October 2026

- Confirmed successful CI run **#109 / run ID `40108599409`** for commit `2681bdcbe75a8d4b19189d9d497dae47306145d7`: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40108599409. Frontend build, backend compilation, CloudFormation lint, and the complete service-replacement test step passed.
- That successful run verifies the employee-ID route restoration at commit `2681bdc...`; it ran before the final route-decorator ordering cleanup described below.
- Follow-up commit `3e294c8314f06c5cb2d01be9caaa8b9fe8a79dbb` reorders the existing profile PATCH decorator and the employee-ID route so each decorator is immediately followed by its intended function (the previous attempt had caused a syntax error caught at compile time).
- CI run for `3e294c...`, run ID `40108723010`, was still **in progress** when last checked: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40108723010. Re-check before treating the latest source head as validated.
- Current PR #3 stays open and draft. Passing automated checks do not prove the running AWS staging Lambda, Cognito callback/provisioning, live database mappings, Preview UI or role boundaries are end-to-end tested.



---

## Continuation update — 24 October 2026, staging auth/access fixes

This section supersedes older status notes above where they conflict. Confirm the current branch/PR/CI state before deploying; do not infer that passing source CI means the AWS backend is updated.

### Verified branch and CI

- Branch: `cognito-staging-integration`
- Verified source head for this update: `024077c6aef11f1e498b065c2011f8206fb50c9d` — commit message `Cover knowledge-only object deletion boundaries`.
- PR #3 remains **open and draft**, base `aws-service-replacements`: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3
- Successful CI run **#125**: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40109613701
- That run passed the pre-token handler test, frontend production build, backend/test compilation, CloudFormation lint, and the isolated service replacement tests, including the employee-ID route, generated-ID/public role spoof prevention and knowledge chat session ownership regression.
- A Vercel status reported the Preview deployment complete for this head: https://vercel.com/divyansh-50b7/enterprise-workplace-assistant/3Z6vMcZrTvR5DvBCw4AbpW5uUyyY. Do not declare visual end-to-end verified: the Vercel tool connection returned 403 when attempting to fetch the protected preview. Current frontend branch alias last known from previous checks: https://enterprise-workplace-assistant-git-cognito-a98678-divyansh-50b7.vercel.app

### Staging database changes applied (project `wxulxcsdpwsyhtpkbazi` only)

- `20261024000000_grant_service_role_profile_privileges.sql`: service_role SELECT/INSERT/UPDATE only on `public.profiles`; no DELETE. Browser roles are not granted profile SELECT.
- `20261024010000_grant_service_role_jobs_select.sql`: missing job read grant was fixed for the trusted backend service role; browser roles still have no direct job SELECT.
- `20261024020000_auto_assign_employee_ids.sql`: stable generated `EMP-######` / `MGR-######` IDs and blank-ID backfill; pre-existing nonblank IDs and profile roles stay unchanged.
- `20261024030000_harden_public_signup_roles.sql`: public metadata cannot self-select Management or spoof employee IDs/management verification. Management must be assigned through trusted Auth admin metadata.
- `20261024040000_grant_backend_service_role_table_privileges.sql`: least-privilege SQL grants for backend repositories using applications, candidates, resumes, candidate scoring, status history and recruiter notes. Browser-role direct SELECT remains denied on those backend-only tables.
- Read-only staging verification showed one profile: `EMPLOYEE`, ID `EMP-000001`, active and not Management-verified. No additional profile was left by the temporary role-spoof transaction test.
- A live transaction probe confirmed that public user metadata requesting `MANAGEMENT`, `SPOOF-999` and `is_management_verified=true` was reduced to Employee with a generated EMP ID and verification false; trusted `raw_app_meta_data` Management assignment resulted in a generated MGR ID and verification true. Probe records were deleted after verification.
- No Production Supabase rows, Production schema, Production Lambda, Production Cognito or the protected `busted` project was altered.

### Source fixes included in the tested branch

- Navbar now uses the same Dicebear Adventurer URL version as the profile page, so the cartoon avatar should render instead of falling back to the initial when the avatar URL works.
- Public signup UIs show Employee self-service and clearly mark Management as administrator-assigned; they do not offer public self-service Management selection. Legacy API signup no longer accepts or copies a client-supplied employee ID.
- Profile reads and edits use authenticated backend APIs, not browser-side direct access to protected `profiles` rows.
- Management dashboard counts and both management/employee onboarding views use protected backend APIs. The onboarding/editor mutations are management-only, and an employee can read only their own onboarding progress.
- Knowledge chat now verifies a session belongs to the current profile before writing a question into it; error responses no longer echo raw downstream errors/chat text. Knowledge-document deletion is confined to knowledge object prefixes and not resume object keys.
- Employee hired/onboarding state is determined from actual hired application status rather than merely the presence of the now-automatically-generated employee ID.

### Existing profiles and login: do not mix environments

- Production profiles remain in the Production Supabase project `ybkfkdcdhrnjmjvavyhb`; they were not copied into staging and were not modified.
- Existing Production users should continue using the current Production application and its configured authentication until a separately reviewed production cutover plan is approved.
- The Cognito identity-link route can link a verified Cognito subject only to a matching profile/Auth identity **within the same Supabase project**. It does not link to a Production profile from the staging project.
- Do not sign up an existing Production user in the staging preview expecting the existing Production profile to appear. If the matching profile isn't in staging, the flow can create a separate staging test profile. A later Production migration must preserve existing profile UUIDs, roles, data and verified email checks.
- Public signup must not be used to create or elevate a Management identity. Use an explicitly trusted admin provisioning path for Management accounts.

### Final deployment gate — requires user action

The code CI and staging SQL migrations are verified, but the backend changes are **not end-to-end complete until the latest backend image is built into ECR, the existing Cognito staging Lambda is updated to that exact image tag, and login/routes are verified in a browser**.

The repository workflow `.github/workflows/build-cognito-staging-ecr.yml` runs only on manual dispatch. The current branch head at this snapshot is `024077c6aef11f1e498b065c2011f8206fb50c9d`; build the image from the current branch head, not the older image tag documented earlier in this file. The workflow writes a unique tag of the form `cognito-staging-<git-sha>` to:

`745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-<git-sha>`

1. Open [GitHub Actions — Cognito staging backend image build](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml).
2. Choose **Run workflow** and select `cognito-staging-integration`. This is the existing workflow, not a new AWS resource; pushing an image adds ECR storage usage, so confirm the expected small but nonzero storage cost is acceptable before running it.
3. After the run succeeds, note its exact `cognito-staging-<sha>` image tag and update only the **existing Cognito staging Lambda** to the matching full image URI. Do not update `enterprise-workplace-assistant-api` (Production). Check the currently deployed CloudFormation stack / Lambda name before saving; do not create a new Lambda/stack or resource.
4. Then run the staging preview flow starting from the actual Vercel branch preview `/signup` route (so the OAuth state/nonce/PKCE cookies are created). Test Cognito signup/login/callback, `EMPLOYEE` role and generated ID, top-right cartoon avatar, profile edit, published-only Jobs, Knowledge Base question access, onboarding visibility, refresh/logout, and Management-only denial boundaries. Use a trusted Management test account only for manager-side routes; never try role elevation through public signup.
5. Check CloudWatch for any sanitized Lambda startup/runtime errors and verify the backend image/deployment version matches the exact SHA used by ECR.

**Do not merge PR #3, change Production, or change `busted` until these manual staging E2E checks pass.** If the Vercel connection remains 403, inspect the preview using the user's own logged-in browser. Do not share passwords, authorization codes, bearer tokens or secrets in chat.


## Continuation update — 24 October 2026 (shared knowledge-document registry)

**Source and validation**
- Working branch: `cognito-staging-integration`; PR #3 stays **open and draft**: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3.
- Source head for the verified code: `485da1dd3e16e6e91509b51db73355e09c384200`.
- CI run #127 passed: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40111103324. Results: **65 passed, 10 warnings**; frontend production build, backend compilation, CloudFormation lint, pre-token handler tests, Cognito/RLS/identity tests, employee-ID/profile route tests, object-storage tests, chat-session ownership tests and new knowledge-document registry tests passed.
- This is an automated/isolated test pass. It is not a live Cognito browser E2E result and does not justify merging PR #3 or switching S3 on.

**Changes in the branch**
- Added migration `supabase/migrations/20261024050000_knowledge_document_registry.sql` and backend-only repository `backend/app/repositories/knowledge_document_repository.py`.
- Knowledge documents now have a shared server-side metadata registry. Authenticated users can list the registered documents; uploads require management access and register filename, provider, durable key, pages/chunks, uploader and internal vector source. The internal Qdrant source path is not returned to the browser.
- S3 upload records use stable keys and keep `file_url=NULL`; they do not persist expiring presigned URLs. The download endpoint can create an expiring URL when it is requested.
- The UI loads the registry and merges legacy localStorage-only documents to avoid dropping old entries. Registered document delete requests use the registry's ID rather than trusting a client-supplied object key.
- Added exact-source Qdrant deletion for registry-backed records and moved DOCX ingestion from Windows-only `pythoncom/docx2pdf` conversion to `Docx2txtLoader`, which works in the Linux Lambda container.
- Knowledge upload validates PDF/DOCX extension and content type, limits upload size to 10 MB, stores the object before indexing, persists metadata, and performs best-effort cleanup of partial writes on failure.

**Staging database migration applied and verified**
- Applied only `knowledge_document_registry` to isolated Supabase project `wxulxcsdpwsyhtpkbazi` (workplace-assistant-staging); migration registry version `20261024162221`.
- A combined read-only query confirmed `public.knowledge_documents` exists with RLS enabled.
- Exact privileges: `service_role` has SELECT/INSERT/UPDATE/DELETE; both `anon` and `authenticated` have none of those privileges. The table is protected by the `knowledge_documents_service_role_only` policy.
- Counts immediately after migration: 1 `auth.users` row, 1 `public.profiles` row, 1 Cognito identity mapping, and 0 registered knowledge documents. Existing staging identity/profile data is unchanged.
- No AWS resources were created or modified for this registry work. `STORAGE_PROVIDER` remains `supabase`; no S3 bucket/cutover has occurred. Production and protected `busted` remain untouched.
- **Next operational blocker:** the running staging Lambda still uses the prior ECR image and does not contain the newly tested `/api/v1/knowledge/documents` registry route. Do not ask the user to test registry UI against that old runtime. Before rebuilding/pushing a new staging ECR image, obtain explicit approval to incur any possible ECR image-storage cost; the user's budget/free allowance cannot be independently confirmed. If approved, run [.github/workflows/build-cognito-staging-ecr.yml](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml) on this branch, then update only the existing staging CloudFormation stack `ewa-cognito-staging-api` / staging Lambda to the new immutable image URI. Preserve its environment and permissions. Do not alter Production.
- Vercel's GitHub status reported the deployment for handoff commit `5f0805dadca463e195c15a76ff2a02e72e0ec1f5` as completed, but direct deployment inspection/API calls from this session returned permission/not-found failures and direct app/API requests were not accessible from this runtime. The authenticated Preview smoke test therefore remains a manual gate after the staging image is updated.

**Next gates**
1. Verify the new branch Preview deployment visually and run one consolidated knowledge smoke test: manager uploads a harmless PDF, employee can see the registered document and request access as expected, S3 mode remains off, and management can delete exactly that document without affecting another same-named document.
2. Then continue the isolated Cognito E2E flow (callback/profile link, employee-vs-management denial, profile editing/ID, Jobs, onboarding, refresh/logout) before any merge/cutover.
3. Only consider S3 staging activation after a separate private staging bucket and least-privilege staging Lambda S3 permissions have been reviewed and the cost is explicitly acceptable. User has no budget; do not create new chargeable AWS resources or switch `STORAGE_PROVIDER=s3` by default.


## Continuation update — 24 October 2026 (post-connection recovery, image slimming, and registry index)

- **Recovery state:** the conversation resumed after a connection interruption. No partially completed AWS deployment was in progress; ECR image push / Lambda update remains intentionally gated.
- **Latest verified application-code SHA:** \`c27aaa846ba143a81ba60ad3939480f7da5c6411\`. CI run #130 passed: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40111719938 — **65 passed, 10 warnings**. Frontend production build, backend/test compilation, Cognito pre-token tests, CloudFormation lint, and the consolidated backend/security/database tests passed. The later commits in this section are handoff/documentation updates only unless a newer source commit is noted.
- **Container slimming:** \`backend/Dockerfile\` no longer installs LibreOffice or Java. Knowledge DOCX ingestion now uses \`Docx2txtLoader\`, and the resume parser also uses \`docx2txt\`; repository search found no remaining runtime use of \`pythoncom\`, \`docx2pdf\`, or \`soffice\`. This reduces unnecessary image packages before the next staging image build.
- **Registry index optimization:** added \`supabase/migrations/20261024060000_knowledge_document_registry_fk_index.sql\` to cover the registry's nullable \`uploaded_by\` foreign key. Applied to staging as migration \`knowledge_document_registry_fk_index\`, version \`20261024163027\`, after the migration regression test passed.
- **Final staging DB verification after both additive migrations:** \`public.knowledge_documents\` has RLS enabled; its \`knowledge_documents_service_role_only\` policy exists; \`service_role\` has SELECT/INSERT/UPDATE/DELETE; \`anon\` and \`authenticated\` have none of those table privileges. Both \`knowledge_documents_created_at_idx\` and \`knowledge_documents_uploaded_by_idx\` exist. Current counts are 1 auth user, 1 profile, 1 Cognito identity mapping, 0 registered knowledge documents; 17 public tables have RLS. No profile or identity records were inserted/changed by these migrations.
- **Supabase advisor review:** the registry's foreign-key-index finding was addressed above. Remaining advisories are pre-existing or intentionally designed: RLS enabled with no policy for \`cognito_identity_mappings\` (intentional fail-closed, service-role-only table); user-scoped \`SECURITY DEFINER\` RPCs \`current_profile_id()\` and \`get_current_user_role()\` are executable to support current-user/RLS behavior; leaked-password protection is disabled in Supabase Auth; and several existing business tables have FK-index, RLS-initplan, unused-index, or multiple-permissive-policy performance findings. Do not broadly change these existing auth/RLS semantics without focused tests and a deliberate migration.
- **Deployment blocker unchanged:** the new backend route and image cleanup are not live until the existing Cognito staging Lambda gets an ECR image built from the verified branch. The GitHub workflow \`.github/workflows/build-cognito-staging-ecr.yml\` is manual-dispatch and pushes an immutable \`cognito-staging-\${github.sha}\` tag. It can incur ECR image-storage charges. Given the recorded zero-budget constraint, do not push or update the Lambda until the user explicitly approves the possible cost. No AWS resource was created or updated during this continuation. The production Lambda, Production environment, and \`busted\` remain untouched.
- **Access limitation:** the current Vercel connector returns HTTP 403 when listing this project's deployments. It cannot independently verify the new Preview deployment from this session; do not claim a live browser E2E result. After the image is built and the existing staging Lambda is updated, use a Preview browser session for the consolidated management-upload / employee-list-and-download / management-delete smoke test, then the broader Cognito auth and role-boundary checks.


## Continuation update — 2026-10-24: staging ECR image pushed

- Approved based on the low, usage-based ECR storage estimate: AWS private ECR storage is listed at $0.10/GB-month beyond applicable allowances; same-region ECR-to-Lambda transfer is free. The exact monthly storage quantity and the user's credit denomination/expiry were not accessible.
- Successfully built and pushed the staging-only backend image through [GitHub Actions run #13](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40113250077). Immutable tag: `cognito-staging-ba091b53ed2d3f6b71e4b54128c894b55da3a35b`. Image URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-ba091b53ed2d3f6b71e4b54128c894b55da3a35b`. Digest: `sha256:ad491e623ae247ddcb180936020c6ab9e3893dd3b525721c13aa17e574dffe46`. Build run completed successfully.
- The temporary one-time push trigger was removed and `.github/workflows/build-cognito-staging-ecr.yml` is restored to `workflow_dispatch` only. The marker file `docs/.staging-ecr-build-trigger` was deleted. No ongoing push trigger remains.
- Updated `infra/aws/cognito-staging-backend.yml` and `docs/COGNITO_STAGING_DEPLOYMENT.md` to point at the verified image tag. CloudFormation lint/test workflow [run](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40113600370) passed for the template change.
- **ECR is the only newly changed AWS resource.** No backend Lambda, CloudFormation stack, Lambda Function URL, or S3 bucket was created or updated. Production Lambda/Vercel/Supabase remain untouched.
- Next blocked step is deploying the separate staging stack `ewa-cognito-staging-api` from `infra/aws/cognito-staging-backend.yml`, then setting Cognito callback/sign-out URLs and branch-specific Vercel Preview settings using the stack outputs. The CloudFormation `SupabaseServiceRoleKey` parameter must contain the *staging* project service-role secret only (it is `NoEcho`; never paste the secret into chat or GitHub files). This template creates an internet-reachable Lambda Function URL and can incur Lambda/log/ECR charges, so check AWS Billing/credit eligibility before creating it.
- This session's available connected tooling did not provide AWS CloudFormation/Lambda control, and the existing GitHub workflow role is only verified for ECR push. Therefore the stack was not deployed and no AWS permissions were guessed or broadened. Resume from the manual deployment gate rather than repeating the ECR build.


## Continuation update — 2026-10-24: outbound TLS and staging cost guard

- Security review found `backend/app/main.py` globally monkey-patched both `httpx.Client` and `httpx.AsyncClient` to use `verify=False`, disabling TLS certificate verification for outbound requests application-wide. Removed this override. HTTPX now uses its normal certificate verification defaults. Follow-up CI run was started for this backend change.
- Added `ReservedConcurrentExecutions: 2` to `StagingApi` in `infra/aws/cognito-staging-backend.yml`. This is a concurrency guard against accidental or abusive simultaneous compute; it is **not** a cap on total requests and does not replace application authentication/authorization.
- Updated `docs/COGNITO_STAGING_DEPLOYMENT.md` to explain the concurrency guard and its limits. The CloudFormation validation workflow is expected to validate the new property along with the full template.
- No live Lambda or CloudFormation stack was created/changed in response to these edits. Production remains untouched; staging deploy still requires a direct CloudFormation action with the staging Supabase service-role secret.


## Continuation update — 2026-10-24: corrected staging image rebuilt

- The first newly built image (`cognito-staging-ba091b53ed2d3f6b71e4b54128c894b55da3a35b`) was superseded because the source still had a global outbound TLS verification override. That older image must not be used for deployment.
- Rebuilt and pushed corrected staging image successfully using [GitHub Actions run #14](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40114757021). Current image URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-5f67a3ec61e09b8dab1181f8b134a1894bb4b4ae`. Digest: `sha256:45d84e98aa8554bae82b8fcd46c500c1d931b736c4da0ac04af7083edf12092a`.
- Confirmed the exact build source commit `5f67a3ec61e09b8dab1181f8b134a1894bb4b4ae` has no `verify=False` override and includes `ReservedConcurrentExecutions: 2` in the staging template present at build time. The live CloudFormation template and deployment guide now point at the corrected tag.
- The ECR workflow has been restored to manual-only and the one-time marker removed again. No image is auto-built on future pushes.
- The final template/doc commits are later than the image's source commit but do not change the backend runtime; a CI run is validating the final CloudFormation default/tag, concurrency setting, backend compile, and regression test suite.


## Continuation update — 2026-10-24: knowledge guest-access hardening and optional S3 IAM

- Added regression coverage and changed the eight read/session/download routes under `backend/app/routers/knowledge.py` to use `require_management_or_employee`, so the synthetic `Bearer guest` identity can no longer list internal document metadata, ask RAG questions, or access knowledge sessions/download URLs. Management-only upload/delete remain management-only. [Latest auth-hardening CI passed](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115351989).
- Completed an additional deployment-template audit. `AWS_REGION` is a Lambda-reserved environment variable and was removed from the template; the Lambda runtime provides it automatically. The earlier intermediate template check failed for that exact reason; the corrected version passed CloudFormation lint in [run #40115264985](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115264985). A newer check is validating the final tag-only template update.
- Extended `infra/aws/cognito-staging-backend.yml` to support optional private S3 storage after a separate bucket exists. Parameters: `StorageProvider` defaults to `supabase`; `DocumentBucketName` defaults blank. Choosing `StorageProvider=s3` requires a bucket name and conditionally attaches only `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on that bucket's `knowledge/*` and `resumes/*`. It creates no S3 bucket, grants no bucket listing/admin/public access, and uses the Lambda execution role (no long-lived AWS keys). The storage change and first-bucket deployment path are documented in `docs/S3_STAGING_SETUP.md`; initial Cognito setup still defaults to Supabase Storage.
- Rebuilt and pushed the **current** staging backend image after the auth fixes: [ECR build run #15](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115342943) succeeded. Image URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-c2141b64f5022cfb86e65859408974cba55fe4f1`. Digest: `sha256:a16bea9c90573a7a7c31150e06a668db3dac041f70db656739d8f7d084cc9def`. Verified image source commit `c2141b64f5022cfb86e65859408974cba55fe4f1` contains no global `verify=False` override and the knowledge guest-access route change.
- `infra/aws/cognito-staging-backend.yml` and `docs/COGNITO_STAGING_DEPLOYMENT.md` now point at this image. The ECR workflow is manual-only again and the temporary build-marker file is removed. Do not use superseded image tags `cognito-staging-ba091b5...` or `cognito-staging-5f67a3...`.
- No Lambda or CloudFormation stack has been deployed; no S3 bucket was created. The remaining manual blocker is creation of the isolated `ewa-cognito-staging-api` CloudFormation stack using the staging Supabase service-role secret, then registering Cognito callback/sign-out URLs and setting branch-specific Vercel Preview values. After that, perform one consolidated browser E2E and do not merge PR #3 until it passes. Production remains untouched.


## Final verification checkpoint — 2026-10-24

- Final CloudFormation/backend regression CI passed: [run #40115477276](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115477276), commit `912587347dbcef700c2008f5153f9b9dbc4109c4`; reported `66 passed, 10 warnings in 2.12s`. The frontend production build, backend compile, Cognito trigger test and `cfn-lint` checks for both AWS templates also passed in this run.
- Final state audit: staging ECR workflow is `workflow_dispatch` only; no temporary push trigger; no `docs/.staging-ecr-build-trigger` file. The current CloudFormation default and runbook both point to the current image tag `cognito-staging-c2141b64f5022cfb86e65859408974cba55fe4f1`. Template does not set Lambda-reserved `AWS_REGION`. Optional S3 IAM policy remains conditional and only covers `knowledge/*` and `resumes/*`.
- The latest code/role-boundary hardening passed in [run #40115351989](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115351989), including synthetic guest rejection across the eight knowledge read/session/download endpoints.
- PR #3 remains open and draft. No backend Lambda, CloudFormation stack, Function URL or S3 bucket is live. The next actual deployment action is the manual creation of `ewa-cognito-staging-api`, with the isolated staging Supabase `service_role` key entered only in CloudFormation’s `NoEcho` field. Then configure the staging Cognito callback/sign-out and branch-specific Vercel Preview variables and run one consolidated browser E2E suite before merging. Keep Production settings and resources untouched.


## Additional security follow-up — hiring account credentials

- Broader route review found `backend/app/services/application_service.py` created hired candidate accounts with a shared hard-coded `Password123!`. Replaced that with `secrets.token_urlsafe(48)`; the generated credential is used only in the Supabase Admin create-user request and is never returned by the API.
- Added `backend/tests/test_application_hiring_security.py` and included it in `.github/workflows/test-service-replacements.yml`. Its regression check asserts the hire-flow password is long, not the shared default, and role metadata remains `EMPLOYEE`.
- Current CI is validating the new test/code. The last ECR image (`cognito-staging-c2141b64f5022cfb86e65859408974cba55fe4f1`) does **not** contain this newest hiring-password fix; rebuild and update the CloudFormation template/runbook image URI only after the new test passes.


## Hiring credential fix and rebuilt final staging candidate — 2026-10-24

- Replaced the hiring flow's shared `Password123!` credential with `secrets.token_urlsafe(48)`. The generated value is used only in the Supabase Admin create-user call and is not returned by the API. Added `backend/tests/test_application_hiring_security.py` and included it in CI.
- The expanded test suite passed: [run #40115982120](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115982120), **67 passed, 10 warnings**; the Next.js production build, backend compile, Cognito trigger tests, and `cfn-lint` for both CloudFormation templates succeeded.
- Rebuilt and pushed the current security-hardened staging image: [ECR run #40115963912](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40115963912). URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-2ae17eda3a6e282c3f497e80233a6d3404f75443`; digest: `sha256:953d6fc2c49019b63ca426e94085c878af0140147635f191e15d64796961b2b6`. Verified the image source contains the random-password fix, the eight knowledge-route guest protections, and no global `verify=False` bypass.
- Updated the CloudFormation image default in `infra/aws/cognito-staging-backend.yml` and the image tag in `docs/COGNITO_STAGING_DEPLOYMENT.md` to this URI. Latest tag-only template CI is [run #40116073644](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40116073644); check its final status before the manual deployment.
- Confirmed the ECR workflow is manual-only and `docs/.staging-ecr-build-trigger` no longer exists. No Lambda/CloudFormation stack, Function URL, or S3 bucket has been created. No Production resources or environment settings were touched.
- Remaining manual gate: deploy `ewa-cognito-staging-api` using the isolated staging Supabase service-role secret in CloudFormation's `NoEcho` field, then configure the Cognito callback/sign-out URLs and the `cognito-staging-integration` Vercel Preview environment from the stack outputs. After that, run the consolidated signup/login/callback/profile-link/employee authorization/RLS/refresh/logout browser E2E suite. Keep PR #3 draft and unmerged until E2E passes.


## Final image and external access gate — 2026-10-24

- The final tag-only template change was validated by [CI run #40116073644](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40116073644): **67 passed, 10 warnings**; frontend production build, backend compile, Cognito trigger tests and CloudFormation lint passed.
- Current deployment image (do not use older tags): `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-2ae17eda3a6e282c3f497e80233a6d3404f75443`, digest `sha256:953d6fc2c49019b63ca426e94085c878af0140147635f191e15d64796961b2b6`. It includes standard TLS certificate verification, guest-rejected knowledge endpoints, and random generated hiring-account credentials instead of the shared default password.
- Current template `infra/aws/cognito-staging-backend.yml` and guide `docs/COGNITO_STAGING_DEPLOYMENT.md` point at that image. Optional S3 is supported with prefix-only object permissions but remains opt-in; `StorageProvider` still defaults to Supabase. Lambda concurrency is capped at 2.
- Confirmed build workflow is manual-only and the temporary marker file is absent. No staging Lambda, CloudFormation stack, Function URL, S3 bucket, or Production resource has been created/changed.
- Vercel preview verification is currently blocked by the connected Vercel integration returning `403 forbidden` at `read_protection_bypass`: it denies access to deployment `dpl_8TZ8EgtRLU3DwZwfbHjtZH94oJwx` and explicitly asks for the Vercel connection to authorize the project/team (or confirm the account's access). No bypass secret or setting was changed. Once access is restored, verify the branch Preview, then proceed with the staging CloudFormation stack and browser E2E.
- PR #3 remains open and draft. Do not merge until the isolated staging API is deployed and the consolidated browser E2E passes.


## Migration continuation audit — 24 October 2026 (current repo inspection)

### Verified repository state
- Active branch: `cognito-staging-integration`; PR #3 remains open/draft against `aws-service-replacements`. PR head when this audit ran: `24b403537df31b278d405926ca04e6823c476af4`.
- Successful service-replacement validation: [GitHub Actions run #40116073644](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40116073644), status `success`, on tested source commit `00534c3cd8363eca8b16ce69faa168281bea22be`. It reports 67 tests passed and 10 warnings, frontend build, backend compile, Cognito trigger tests, and CloudFormation lint. The current PR tip after that run has a later documentation-only commit; do not describe this as a fresh test run on SHA `24b4035`.
- Latest listed Vercel Preview for `cognito-staging-integration` is Ready on commit `24b403537df31b278d405926ca04e6823c476af4`, but the connected Vercel integration refused protected deployment inspection with HTTP 403. Branch-scoped env values and actual rendered UI therefore remain unverified from this session. Do not infer Cognito is switched on in Preview.
- Live Supabase staging project `wxulxcsdpwsyhtpkbazi` (region ap-south-1) is ACTIVE_HEALTHY. Direct read-only verification shows 17/17 public base tables have RLS enabled; `knowledge_documents` is present with its service-role-only policy; browser-facing roles `anon` and `authenticated` have no table privileges on it; `service_role` has SELECT/INSERT/UPDATE/DELETE. Registry and FK-index migrations are recorded as applied. Current counts: 1 Auth user, 1 profile, 1 Cognito identity mapping, 0 registered knowledge documents.
- Production Supabase `ybkfkdcdhrnjmjvavyhb` and protected project `busted` `zkxpkjgprewurotifgeh` were not changed. Keep them untouched.

### Current migration architecture and scope
- Next.js 15 App Router frontend; FastAPI backend; Supabase PostgreSQL/Auth/Storage; Gemini; Qdrant Cloud. Do not migrate to RDS. Cognito remains opt-in and is intended to preserve database profile UUIDs/application roles through a server-only `cognito_identity_mappings` table.
- Cognito source code covers RS256/JWKS validation, separate access/ID token validation, issuer/expiry/app-client/token-use checks, ID-token nonce and verified email, profile linking/provisioning as EMPLOYEE, database-derived application role/active status, PKCE/state/nonce cookies, refresh and logout.
- Backend role protections include manager-only hiring/admin actions, employee ID operations, knowledge upload/delete, manager-only onboarding mutations, and guest-denial regression checks. Supabase browser table grants were deliberately removed for backend-owned hiring data; backend uses service_role with application-level route checks.
- Knowledge documents now have a shared backend-only registry and stable object key. S3 adapter/template is optional, with object-level actions only under `knowledge/*` and `resumes/*`; S3 is not activated and no S3 bucket should be created under the zero-budget constraint. Supabase Storage remains the default.

### Critical deployment facts — reconcile older notes
- The ECR workflow `.github/workflows/build-cognito-staging-ecr.yml` is `workflow_dispatch` only. It pushes a staging-tagged image; it does not deploy or update Lambda. Its last handoff-listed image is `cognito-staging-2ae17eda3a6e282c3f497e80233a6d3404f75443` (digest `sha256:953d6fc2c49019b63ca426e94085c878af0140147635f191e15d64796961b2b6`). The code branch later added the knowledge-document registry integration and other code; do not assume the listed image contains code added after that build. A new image would be required for new runtime code.
- The handoff contains conflicting older statements about the staging API: one dated milestone says stack/Lambda was deployed and gives a Function URL; later and final sections say no staging stack/Lambda/Function URL was created. Latest PR #3 comments also describe the running Lambda as older than knowledge-registry code. This session has no AWS CloudFormation/Lambda read-write tool to establish the real resource state; verify the AWS console before any update. Never create a new stack/function just to resolve this conflict.
- Vercel deployment listing knows a Ready deployment, but protected deployment reads returned 403; environment listing returned not-found. Ask for Vercel integration project/team access to be repaired, or inspect the Preview from the user's own signed-in browser. Never bypass deployment protection.
- Do not modify `main`, Production Lambda, Production Vercel settings, Production Supabase, or `busted`. Do not push another ECR image or deploy/update Lambda while costs remain unapproved/unverified. No secret values should be shared in chat.

### Findings from code and live schema review
- Security improvements in branch include removal of the global HTTPX `verify=False` override, cryptographic Cognito JWT verification, prevention of public metadata from granting MANAGEMENT or spoofing IDs, replacement of a shared hire-flow password with a random per-account secret, service-role-only storage grants, and guest denial on knowledge endpoints. These are source/CI findings, not live end-to-end proof.
- The live Supabase security advisor calls out `current_profile_id()` and `get_current_user_role()` SECURITY DEFINER helpers. Read-only privilege checks confirmed `anon` and `authenticated` can execute `current_profile_id()`; `get_current_user_role()` is effectively executable through PUBLIC. These were intentionally made callable for current-user/RLS use in the Cognito migration, so do not revoke privileges speculatively. Perform a focused review/test: confirm each helper can reveal only the caller's own mapping/profile/role under both Supabase and Cognito JWTs, then decide whether moving them to a non-exposed schema or restricting direct RPC invocation can preserve RLS behavior.
- README describes department-level filtering for Knowledge/RAG, but current `backend/app/services/knowledge_rag.py` runs an unfiltered similarity search over the shared `knowledge_embeddings` Qdrant collection, and the metadata registry has no department/access-scope field. The promise is not currently evidenced by code. Before claiming enterprise department isolation, define the desired scope model and add metadata + query filtering/authorization tests. Do not retroactively assume every document is global or department-private without product requirements.
- `backend/app/routers/knowledge.py` has safe server-side authorization and shared registry behaviour, but its delete/list/download paths still need a real runtime smoke test against the current image; zero registry rows means the new workflow has not been exercised end to end.
- Supabase Auth leaked-password protection is disabled in the live staging advisor; enabling is a dashboard/auth-policy change, not completed by repository code. Review before wider signup rollout. Other advisor messages include baseline index/RLS/performance findings; do not bulk-edit existing policies without tests.

### Next action / gates (use this order)
1. Repair Vercel connector authorization for team `divyansh-50b7` / project `enterprise-workplace-assistant`, or use the user-owned browser to verify the branch Preview and its branch-scoped environment variables. Do not change Production.
2. Confirm, in AWS console, whether stack `ewa-cognito-staging-api` and function `ewa-cognito-staging-api-StagingApi-xlm7Nj337FcE` actually exist, the current resolved image digest, staging-only environment values, and one health response. If it doesn't exist, do not create it without an explicit cost decision. If it exists, determine whether current code is behind before updating.
3. Keep ECR build manual-only. Only build and update the existing staging Lambda after explicit acceptance of non-zero ECR/storage/compute/log costs and a rollback plan. Enter the staging Supabase service-role secret only into the CloudFormation NoEcho field, never into chat/GitHub. Keep `StorageProvider=supabase`.
4. Run one consolidated browser staging check (not repetitive micro-tests): app-originated Cognito signup/login → callback PKCE/state/nonce → profile/mapping → employee API; verify manager-only action denied for employee; profile/employee ID, published-only jobs, management/dashboard/onboarding endpoints; knowledge list/upload/download/delete using one harmless test file; refresh/logout; inspect one correlated sanitized Lambda log. Check DB counts afterwards, delete only test data if safe.
5. Before enterprise release, decide and implement document access scope/department filtering in Qdrant; review SECURITY DEFINER RPC exposure and leaked-password protection; then run final CI and keep PR #3 draft until the E2E tests and review pass.


## Requirements traceability and migration progress — 24 October 2026

This section explicitly maps the requested migration requirements to implementation evidence and remaining work. The percentage figures are planning estimates, not test coverage metrics. "Implemented" means the repo/configuration contains the work; it does not mean the live service has passed end-to-end validation.

### Required scope checklist

| Requirement | Evidence in current branch | Completion estimate | Remaining before complete |
|---|---|---:|---|
| **AWS IAM for workload access and role-based security** | The successful manual ECR workflow assumes `GitHubActions-EWA-Cognito-Staging-ECR` through GitHub OIDC and can push to the staging backend ECR repository. `infra/aws/cognito-staging-backend.yml` defines a separate Lambda execution role with bounded CloudWatch log-write actions and an optional S3 object policy for only `knowledge/*` and `resumes/*`. FastAPI dependencies enforce Management/Employee boundaries; application roles come from the database profile, not AWS IAM roles or browser/Cognito privilege claims. | **65%** | Verify the deployed Lambda execution role/trust/policies against the template; exercise employee/management positive and negative access paths on the live staging API; ensure no broad browser table grants or Production IAM changes. |
| **Private S3 storage for resume submissions** | `backend/app/routers/resume.py` calls the storage adapter with prefix `resumes`; S3 stores a stable `resumes/...` key, the relational resume record stores an `s3://...` locator, the candidate repository creates a short-lived URL for authorized candidate detail, and the hiring/screening route can download S3 resume bytes. `backend/app/services/object_storage.py` has scoped resume URL/download helpers. | **55%** | No live private staging bucket/cutover is confirmed. Verify resume submit → object key → candidate/resume records → authorized presigned download → screening → deletion/cleanup. Keep Supabase Storage as fallback and default. |
| **Private S3 storage for company-policy/chatbot documents** | `backend/app/routers/knowledge.py` uploads PDF/DOCX via the `knowledge` prefix, indexes content into Qdrant, and stores durable metadata in `public.knowledge_documents`. S3 keys use `knowledge/...`; presigned download links are minted on demand. The bucket template enables Block Public Access, SSE-S3 and a TLS-only policy. | **55%** | No private bucket or S3 live upload is verified; registry count is currently 0. Test upload/list/read/delete and Qdrant cleanup with one harmless document. Add and test department/document scope filtering before enterprise-wide rollout. |
| **Cognito sign-up/sign-in workflow** | Frontend starts authorization-code OAuth with PKCE, state and nonce; callback validates cookies, exchanges the code, calls the API identity-link/provision route and stores app session cookies. Backend validates Cognito tokens and maps `sub` to the existing profile; public signup is forced to EMPLOYEE. Pre-token V2_0 handler is documented as deployed and its mock test passes. | **60%** | An app-originated browser flow has not been demonstrated end to end. Verify callback URL + Preview environment, token exchange/nonce, account provisioning/linking, profile fetch, role enforcement, refresh and logout with one staging account. |
| **Isolated AWS Lambda backend** | Containerized FastAPI backend and ECR-only staging build workflow exist. `infra/aws/cognito-staging-backend.yml` defines the Cognito-enabled staging API, staging-only Supabase secret parameter (`NoEcho`), CORS origin, separate execution role and concurrency limit. The image candidate most recently recorded in this handoff is `cognito-staging-2ae17eda3a6e282c3f497e80233a6d3404f75443`, digest `sha256:953d6fc2c49019b63ca426e94085c878af0140147635f191e15d64796961b2b6`. | **50%** | Historical handoff entries disagree about whether the stack/function has already been created or updated. Verify the existing `ewa-cognito-staging-api` stack, function `ewa-cognito-staging-api-StagingApi-xlm7Nj337FcE` if present, resolved image digest and health response in AWS. Do not create a duplicate stack/function. Do not assume the ECR push deploys Lambda. |
| **CloudWatch monitoring/logging** | The staging CloudFormation template provisions `/aws/lambda/ewa-cognito-staging-api` with 7-day retention and a Lambda execution-role policy for log stream creation and event writes. Previous production handoff reports CloudWatch Logs already exist. | **40%** | Verify the actual staging log group and a real correlated invocation/error event. No staging Lambda error/latency/throttle alarms are defined in the template. Decide whether low-noise alarms are useful only after checking cost; do not claim the live runtime is healthy from CloudFormation status alone. |
| **Keep existing core services and protect Production** | Supabase PostgreSQL/Auth/Storage, Gemini and Qdrant remain the intended baseline; no RDS migration. Branch-specific staging is intended to leave Production Vercel, Lambda, Supabase and the protected `busted` project unchanged. | **80%** | Re-verify actual AWS/Vercel state before changes because connected deployment inspection is currently blocked. Preserve legacy Supabase Auth/Storage as default until staging proof and rollback steps pass. |
| **Knowledge department/document-scope filtering** | Implemented in branch source: management selects `ALL` or a department at upload; `knowledge_documents.department_scope` is persisted; Qdrant chunks carry normalized `metadata.department_scope_key`; employee retrieval is filtered to `ALL` plus their profile department; document listing and signed downloads enforce the same scope; unscoped Qdrant points fail closed for employees. Additive migration is applied to isolated staging Supabase. | **75% implementation; E2E pending** | Verify CI on latest fail-closed commit; runtime-test global vs department retrieval against the configured Qdrant collection; re-index/re-tag old unscoped documents before employees need them; confirm signed-download and cross-department denial through staging API. Staging registry currently has 0 rows, so upload-to-Qdrant-to-query has not been live-tested. |

### Progress estimate

- **Source implementation for requested migration:** roughly **78%**. Cognito flow, token verification, server-side app RBAC, storage-provider abstractions, resume and knowledge-storage paths, CloudFormation templates, OIDC/ECR build workflow, schema migrations, and focused CI tests are present.
- **Staging infrastructure/configuration alignment:** roughly **45%**. Staging Cognito and Supabase integration pieces are documented and some live database work is verified, but Lambda deployment state conflicts between handoff entries and Vercel branch environment inspection is blocked.
- **End-to-end verification/release readiness:** roughly **25%**. The consolidated application-originated Cognito test, live resume-to-S3 test, knowledge upload/download/delete test, real CloudWatch correlation, and cross-department retrieval test remain unproven.
- **Overall migration completion estimate: about 58%.** This is a weighted planning estimate, not a measured percentage of code. Core implementation is ahead of operational proof; do not merge/cut over based on the estimate alone.

### Current evidence from this continuation
- The latest inspected source/test workflow was [run #40116073644](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40116073644): success, 67 tests passed, 10 warnings; frontend build, backend compile, Cognito trigger tests and CloudFormation lint succeeded. It ran on tested code commit `00534c3cd8363eca8b16ce69faa168281bea22be`, not on any later documentation-only SHA.
- The connected Vercel API reported a Ready deployment for the current branch head, but direct protected deployment inspection returned 403. Therefore the rendered UI and live branch-scoped environment variables were not verified here.
- Direct read-only Supabase staging queries confirmed 17/17 public base tables have RLS; the `knowledge_documents` table is RLS-enabled and service-role-only; the current registry count is zero. Current observed counts are 1 Auth user, 1 profile and 1 Cognito identity mapping.
- No AWS CloudFormation/Lambda control or CloudWatch log-read tool is available through the current connected tools. Stack existence, deployed image digest, live API health and correlated CloudWatch behavior require AWS-console access. This is the next external verification gate; do not create a duplicate stack based on stale handoff notes.

### Next implementation milestone (continue autonomously)
1. Add a focused regression test around the resume upload's object-storage persistence/cleanup path and fix orphaned S3/Supabase resume objects if database persistence fails after upload.
2. Keep `docs/aws-role-access-matrix.md` aligned with the Cognito staging branch and this matrix; do not describe Cognito as entirely unimplemented when the source exists, while still labelling browser E2E pending.
3. Add a later source milestone for knowledge department scope after the intended global-vs-department document model is settled from the current README requirement; use fail-closed behavior and cross-department negative tests.
4. Do not change Production, create an S3 bucket, or create/update Lambda until the actual AWS stack/image state and the relevant cost/resource implications can be checked. No credentials or service-role keys may be shared in chat.

## Continuation milestone — requirements and department-scope implementation (24 October 2026)

This section supersedes older notes in this file that describe department/document-scope filtering as unimplemented. Estimates remain planning judgments, not measured code coverage. Implemented, CI-tested, deployed and end-to-end verified are deliberately separate states.

### Requirements matrix — current milestone update
- **AWS IAM:** Separate GitHub Actions OIDC/ECR build identity from the Lambda execution role. The staging execution role is scoped to CloudWatch log writes and optional object-level S3 operations only for `knowledge/*` and `resumes/*`. Application Management/Employee permissions are still enforced by FastAPI and database profile roles; they are not AWS IAM identities. Runtime role policy still needs to be inspected in AWS.
- **Resume submissions:** `/resume/upload` writes the file through the configured provider under the `resumes` prefix, stores an S3 key rather than a permanent presigned URL, and candidate-detail access creates a short-lived URL. If database persistence fails after upload, the route now attempts prefix-validated object cleanup. Regression tests cover provider-specific cleanup and the failure/success repository paths. **S3 is not live-cut-over**; the provider remains Supabase.
- **Chatbot/company policy documents:** Management can select `ALL` or an explicit department on upload. Storage uses the `knowledge` prefix; Qdrant chunks receive `metadata.department_scope_key`; the database registry stores a `department_scope`. Employee query filtering allows only company-wide `ALL` documents and documents matching the employee's department. Document listing and signed S3 download URL creation apply the same scope policy. New unscoped Qdrant points are excluded from employee retrieval (fail-closed).
- **Cognito sign-up/sign-in:** OAuth authorization code with PKCE/state/nonce, token validation, identity mapping and database-backed role resolution are implemented in source. Browser callback, profile linking, session refresh/logout and employee/manager denial paths still require a consolidated live staging test.
- **Lambda:** The opt-in CloudFormation template defines the isolated staging Function URL/API runtime and reserved concurrency of 2. ECR build workflow is manual-only and does not deploy Lambda. The actual deployed stack and image digest are unresolved because historic handoff notes conflict; do not create a duplicate or assume a push updated the function.
- **CloudWatch:** Staging template defines `/aws/lambda/ewa-cognito-staging-api` with 7-day log retention and a least-privilege logging policy. Live invocation/log correlation is not verified. The template does not currently define error/throttle/latency alarms; keep that explicit in release readiness instead of claiming alarms are present.
- **Database and scope migration:** Applied `20261024070000_knowledge_document_department_scope.sql` to the isolated staging Supabase project `wxulxcsdpwsyhtpkbazi`. Live read-only checks confirmed `department_scope TEXT NOT NULL DEFAULT 'ALL'`, the index `knowledge_documents_department_scope_idx`, RLS enabled, no SELECT privilege for `anon` or `authenticated`, and SELECT privilege for `service_role`. Registered document count is 0. Production project `ybkfkdcdhrnjmjvavyhb` and protected project `busted` were not changed.
- **Private S3 bucket:** Still not created, because provisioning may incur costs and AWS control access is not available through this session. The template and provider code are ready for staging configuration, not proof of a live bucket.

### CI and deployment evidence — exact boundaries
- [Run #159](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40119120676) passed on `4b27f85c6084a380a6c6e78fa8f87a27f39f76f9`; this covered the resume-storage cleanup change.
- [Run #162](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40119680287) passed on `32e7b5a41378710b8755fc6cfe73f5f4ddfe9b79`. The full job's Cognito trigger test, frontend install/build, backend compile, CloudFormation lint and test suite all completed successfully. It includes initial department-scope filtering and focused cross-department route tests.
- New security-hardening commit `9affd666aa93011d007d1cedacd43ce69d78bb2b` removes missing-scope Qdrant points from employee search, and hides unscoped localStorage entries from employees while leaving them visible to management for review/re-upload. [Run #163](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40119796132) was still in progress at the last inspection; do not mark this exact commit green until the run finishes.
- Vercel status for the latest commit reports `Deployment rate limited — retry in 24 hours`. Therefore no new Preview bundle was produced for the latest commits; GitHub Actions CI is independent of that restriction. The previously listed Preview being Ready does not prove that it contains the latest department-scope code or environment variables.
- The two earlier failed CI runs are recorded for debugging only: run #160 failed on the then-current first scope version; run #161 caught an incorrect test assertion about Qdrant's `FieldCondition.key` shape. Those specific test defects were corrected; run #162 then passed on the corrected prior commit.

### Updated completion estimate
- **Source implementation: ~75%.** Cognito/RBAC, storage abstractions, resume object rollback, department scope metadata/filtering, frontend scope selector, additive schema migration, and regression tests now exist.
- **Staging infrastructure/configuration alignment: ~45%.** Database schema is verified, but S3 bucket, Lambda stack/image alignment, Vercel Preview config and real CloudWatch events remain unconfirmed.
- **End-to-end/release proof: ~25%.** Live Cognito callback, resume upload through staging, policy upload/index/query/download/delete, real cross-department RAG denial and CloudWatch correlation are not proven.
- **Overall migration estimate: ~58%.** This estimate moved up from 55% because meaningful source/security work and the additive staging schema migration have landed. It is still not release-ready: operational verification is the main remaining gap.

### Next steps — continue from here
1. Run #163 passed on `9affd666aa93011d007d1cedacd43ce69d78bb2b`; later milestones and the latest exact CI checkpoint are recorded in the continuation section below.
2. Once CI passes, review/apply any required staging-only code/schema alignment and prepare a single consolidated staging test. The live `knowledge_documents` count is 0, so use harmless sample documents only when the current deployed API/runtime and Qdrant target can be verified.
3. Re-tag/re-index legacy/unscoped Qdrant documents with `ALL` or an explicit department. The fail-closed policy means legacy points without `metadata.department_scope_key` must not be served to employees until this is done.
4. External manual gates only: Vercel Preview build is rate-limited for 24 hours; AWS console access is needed to verify existing stack/function/image digest, S3 bucket state, environment and CloudWatch logs. No manual test or approval is needed for further repository-only work.
5. Keep PR #3 draft and do not merge. Do not create a bucket, create a second Lambda stack/function, incur avoidable AWS charges, or change Production while infrastructure state remains unverified.

## Continuation milestone — private storage URLs and legacy resume compatibility (24 October 2026)

### Source changes and verified test results
- [CI run #163](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40119796132) passed on `9affd666aa93011d007d1cedacd43ce69d78bb2b`; it validates fail-closed filtering of unscoped Qdrant points and the frontend legacy-document scope filter.
- [CI run #164](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40120123342) passed on `61945ef29fb36de2a89d19423e7cba956d2c1e16`: **93 tests passed, 10 warnings**, frontend build passed, backend compilation passed, and both CloudFormation templates passed `cfn-lint`.
- [CI run #165](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40120198772) passed on `154c4cb64970b799cee1fc303157a54a4e5bbb73`: **94 tests passed, 10 warnings**, frontend build passed, backend compilation passed, and CloudFormation lint passed.
- Supabase storage provider now persists stable keys for newly uploaded knowledge documents and resumes; it no longer emits a public URL during upload. Signed URLs use the official Supabase Storage `create_signed_url(path, expires_in)` API and are generated after server-side access checks.
- The knowledge download route now supports the S3 and Supabase providers using the trusted `knowledge_documents` registry and the same department visibility check. The API no longer returns stored storage URLs in registry responses.
- Resume rows created by new code store `s3://...` or `supabase://...` stable locators. Authorized candidate-detail retrieval creates a short-lived provider-specific signed URL. The hiring pipeline downloads Supabase-stored files through the backend storage client.
- Compatibility is preserved for legacy resume rows with recognized Supabase Storage URL paths: the backend extracts only the known bucket-relative key, validates the `resumes_` prefix, and creates a signed URL or downloads through the backend. The supplied URL is never fetched directly.

### Live staging checks
- Supabase project `wxulxcsdpwsyhtpkbazi`: the `resumes` Storage bucket exists with `public=false`. This is a read-only metadata check; no file was uploaded, read or deleted.
- The additive `knowledge_documents.department_scope` migration is applied and verified. RLS is enabled; `anon` and `authenticated` have no direct SELECT on the registry, while `service_role` retains SELECT. Registry row count remains 0.
- No S3 bucket has been created; `STORAGE_PROVIDER` remains `supabase` by default. No Lambda stack/function was created or changed, and no Production resources were modified.

### Completion estimate and what is not yet proven
- **Source implementation: ~78%** — Cognito auth paths, database-backed application roles, role checks, object-storage adapter for S3/Supabase, private signed downloads, resume object cleanup, department-scoped Qdrant ingestion/retrieval, schema migrations, and regression tests are present.
- **Staging infrastructure alignment: ~45%** — schema and staging bucket privacy are verified, but actual Lambda stack/image/environment and CloudWatch event/log correlation remain unknown. S3 cutover remains unconfigured.
- **End-to-end/release verification: ~25%** — CI passing does not prove a deployed browser flow, actual Qdrant retrieval isolation, live upload/download/delete, or CloudWatch runtime health.
- **Overall migration estimate: ~58%**. The source implementation is stronger, but the unresolved operational state is still the limiting factor. Do not merge or cut over based on CI alone.

### Next gates
1. The latest green source checkpoint is run #165, SHA `154c4cb64970b799cee1fc303157a54a4e5bbb73`. Any further source change must be followed by CI and a handoff update.
2. Vercel says Preview deployment is rate-limited for 24 hours. Do not keep pushing cosmetic/document-only commits merely to force a Preview. After the limit clears, confirm the current Preview uses the staging API and staging Supabase variables before testing login.
3. AWS console verification remains required to determine whether `ewa-cognito-staging-api` and its function already exist, confirm the deployed image digest and staging configuration, and inspect a real CloudWatch invocation. The connected tools in this session cannot perform those AWS-console checks.
4. After the runtime is verifiably aligned, run one consolidated staging test: Cognito signup/login/callback/refresh/logout, role-bound API checks, resume upload/detail/screening, company-policy upload/index/retrieval/download/delete with `ALL` and department-specific documents, cross-department denial, and one correlated CloudWatch log.
5. Existing Qdrant points without `metadata.department_scope_key` stay hidden from employee retrieval until management re-tags/re-indexes them. The registry count of 0 means this path has not been proven with a live document. Keep PR #3 draft and do not change Production or provision chargeable AWS resources.

## Latest verified checkpoint — fail-closed scope default and CI green (24 October 2026)

### Current branch and verification
- Current source head at this checkpoint: `27ad53a2614469cf0d1d8bd6abd2c2a32f17cc12`.
- [GitHub Actions run #168](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40120527091) passed on that exact SHA. Frontend build, backend compile, CloudFormation template lint, and the service-replacement tests succeeded: **97 passed, 10 warnings**.
- [Run #167](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40120428488) passed on `339051022863cdf1f6bdf661c79e6fb1d9187eb8`: **97 passed, 10 warnings**. It covers candidate-detail signing for current and legacy Supabase resume locators and prefix-validated private resume downloads.
- [Run #166](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40120400099) passed on documentation/setup commit `e5eee9cd0bd53785b8e273a652b4e247f00cf7bb`.
- Vercel rate limiting remains on new branch commits. A green GitHub Actions run does not mean the latest code is deployed to a new Preview; the latest Preview environment and running application are still unverified.

### Fail-closed database scope rule
- Applied `20261024080000_knowledge_document_scope_fail_closed_default.sql` to the isolated staging project only. It changes the default for `knowledge_documents.department_scope` from `ALL` to `REVIEW_REQUIRED`, so a future writer that omits the scope cannot accidentally create a company-wide document.
- A read-only live query confirms `department_scope TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED'`. The application visibility helper denies `REVIEW_REQUIRED` documents to employees while Management can still see them for review/retagging.
- This migration changes only the column default and does not rewrite existing rows. The staging registry currently has 0 documents.
- The earlier `20261024070000_knowledge_document_department_scope.sql` migration remains applied and created the scope column/index. If any existing registered rows are later found, review their scopes explicitly rather than assuming department ownership.
- Current staging security verification remains: RLS enabled on `knowledge_documents`; `anon` and `authenticated` have no SELECT privilege; `service_role` has SELECT; registry row count 0. The staging Storage bucket `resumes` is recorded as `public=false`.
- Production Supabase `ybkfkdcdhrnjmjvavyhb`, protected project `busted` (`zkxpkjgprewurotifgeh`), Production Lambda, Production Vercel settings, and `main` were not changed.

### Updated completion assessment
- **Repository/source implementation: approximately 80%.** Cognito token/linking code, profile-backed app RBAC, IAM role template separation, opt-in S3 paths for resumes and Knowledge documents, scoped signed downloads for S3/Supabase, resume object cleanup, department-aware Qdrant filtering, fail-closed default, and regression tests are present.
- **Staging infrastructure alignment: approximately 45%.** Database migrations and private staging bucket metadata are verified. Actual Lambda stack/function existence, deployed image digest/environment, current Vercel Preview variables, and real CloudWatch invocation logs remain unresolved.
- **End-to-end/release readiness: approximately 25%.** CI is green, but the live Cognito callback, actual API runtime alignment, resume upload/detail/screening, Knowledge upload/index/query/download/delete, cross-department retrieval denial, and CloudWatch correlation are not proven.
- **Overall migration estimate remains approximately 58%.** This is a planning estimate, not code coverage. Operational proof is still the bottleneck; do not merge or switch Production based on source CI alone.

### Next steps (priority order)
1. **AWS-console gate:** Inspect existing CloudFormation stack `ewa-cognito-staging-api` and function `ewa-cognito-staging-api-StagingApi-xlm7Nj337FcE` if present; confirm resolved image digest, staging environment variables, execution-role policy, and a health response. The current connected tools cannot inspect/update Lambda or read CloudWatch logs. Do not create a duplicate stack/function.
2. **Preview gate:** Vercel currently reports deployment rate limiting for 24 hours. After it clears, confirm the latest branch Preview points only to staging Supabase and staging API. Do not bypass deployment protection or alter Production variables.
3. **Consolidated staging test:** Once runtime alignment is verified, use one harmless company-wide policy, one department-scoped policy, and one synthetic resume. Test Cognito signup/sign-in/callback/refresh/logout, employee-versus-management route permissions, document upload/index/query/download/delete, cross-department denial, resume detail/screening, and one correlated sanitized CloudWatch event.
4. **Legacy Qdrant data:** Points without `metadata.department_scope_key` are deliberately excluded from employee retrieval. Management must re-tag/re-index them with `ALL` or an explicit department before employee use. Do not loosen the filter.
5. **Cost and guardrails:** S3 remains opt-in; no bucket was created. `STORAGE_PROVIDER` remains Supabase by default. Keep PR #3 draft and do not change Production or create chargeable AWS resources while AWS state and costs remain unverified.


## Continuation — explicit Employee / Management selection and access diagnosis (25 October 2026)

### Product role flow clarified
The account-creation UX must explicitly ask whether the person needs **Employee** or **Management** access. This is an application-role decision, not a request to give the browser user AWS IAM credentials. Cognito verifies identity; the relational `profiles.role` remains the source of truth for application authorization; FastAPI enforces it on every protected operation. AWS IAM belongs to Lambda's execution role, GitHub Actions' ECR publishing role, and tightly scoped resource permissions. Do not map public user choice directly to unrestricted AWS IAM permissions.

### Root-cause boundary for the reported “Cognito signup worked, but app access didn't”
The previous hosted Cognito test authenticated successfully but redirected to the old CloudFront root instead of the Next.js `/auth/callback`. That bypassed OAuth state/nonce/PKCE completion and the `COGNITO_LINK_API_URL` identity-link/provision endpoint. The last audit also found the branch Vercel Preview pointed `NEXT_PUBLIC_API_URL` at `https://example.invalid`, while Cognito mode was still off. A valid Cognito user can exist without an app session/profile mapping or a working backend route. The successful hosted login alone does not prove API access.

### Source changes added in this continuation
- Cognito signup now presents explicit Employee and Management access choices.
- A selected Management level is safely handled as a request, never as a role supplied by a browser. New identities are first provisioned as EMPLOYEE; Management elevation can only be approved by an already-active Management profile. This prevents public self-registration from granting privileged access to every caller.
- Added server-only `management_access_requests` schema/table and a database function that atomically approves/rejects a pending request. Approval independently checks the reviewer's active database role and only promotes an active EMPLOYEE; it sets `is_management_verified=true`.
- Added backend endpoints to check/submit/resubmit the caller's request and a Management-only pending-request inbox/review route.
- Added a Settings access-request status/inbox UI and exposed Settings & Access in the profile dropdown.
- Added regression tests for role-claim rejection, request idempotency, rejected-request resubmission, atomic DB promotion/role checks and Cognito link behavior.
- CI failed on the first test iteration due to a missing `pytest` import and a migration file not yet present at the time that intermediate commit's workflow was checked out. The import is fixed and migration is now on the branch; verify the newest CI run against the current head before treating it as green.

### Application role vs AWS IAM
- `EMPLOYEE` / `MANAGEMENT` is the application role in `public.profiles.role`; route dependencies and data-scope filters enforce these permissions.
- Cognito user-pool groups/token claims are not by themselves authoritative for application privileges in this design. Only the database profile role is used after validating the token and mapping the Cognito `sub`.
- Lambda's execution IAM role may access only the explicitly configured private storage prefixes and CloudWatch Logs; GitHub OIDC roles build/push ECR images. Do not give employees/management AWS access keys or general S3 IAM credentials.
- If the product later requires instant, self-service selection of Management at signup, that requires a separate trust mechanism (for example an administrator-issued invitation or verified organization provisioning). Plain public self-selection is a privilege-escalation path and must not directly write the Management role.

### Remaining manual/infra gates
- Inspect the current head and wait for CI to complete; no merge until all tests pass.
- The current branch-specific Preview/API configuration and Cognito redirect must be confirmed. The last handoff says a Vercel build rate limit prevented a fresh Preview and the Cognito staging backend CloudFormation stack is not deployed. Do not use Production variables or point this Preview at the Production API.
- After the appropriate AWS cost/billing guard, deploy or update only the isolated `ewa-cognito-staging-api` stack using the staging Supabase key supplied directly in CloudFormation `NoEcho`. Then set exact Preview `/auth/callback` and `/login` URLs and the staging API/link URL, redeploy Preview, and test sign-in, profile mapping, Employee access, a Management-only denial, request approval and logout.
- S3 remains opt-in. Do not create the bucket or set `STORAGE_PROVIDER=s3` until costs, current stack state and private-bucket permissions are checked.


## Latest validated continuation — 25 October 2026

- Latest fully green backend/frontend/CloudFormation CI for the Management access implementation: [run #40124285714](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40124285714), branch commit `9c091bbb6d06a92a8f9169806de402a6d4f5b836`: **112 passed, 10 warnings**. The subsequent branch head `30d23c5d4cf1640db4664332818a209e2fcde523` changed only documentation, not application code.
- The private staging migration `management_access_requests` was applied to project `wxulxcsdpwsyhtpkbazi` and verified: RLS enabled; no client-role read or RPC execute privilege; server `service_role` has the required access. The request table contains zero rows.
- The current Cognito signup asks Employee/Management. A verified email configured in the staging Lambda's `COGNITO_MANAGEMENT_EMAIL_ALLOWLIST` can be granted Management immediately by server-side logic; other Management selections remain Employee and create an approval request.
- Branch-specific Vercel Preview variables are configured for Cognito, the exact `/auth/callback`, the isolated staging Supabase project, and the staging Lambda URL. The latest checked Ready frontend deployment contains the source UI, but the live Lambda image/config and a browser-based sign-in + role authorization test remain unverified.
- The previously used ECR tag `cognito-staging-2ae17eda3a6e282c3f497e80233a6d3404f75443` predates the newest Management bootstrap code. The CloudFormation `ImageUri` parameter is now required so an old image is not accidentally selected. Build the current branch via the manual ECR workflow and update only the isolated staging stack before E2E. Keep `StorageProvider=supabase`; do not create a bucket or touch Production.


## Final CI / staging checkpoint — 25 October 2026 (supersedes older snapshots above)

- Current source/template checkpoint `961adefa90ddab9195b1102a453998ff8a64b4e6` passed [GitHub Actions run #40124516406](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40124516406): **112 tests passed, 10 warnings**; Cognito trigger tests, frontend build, backend compile, CloudFormation lint and backend regression suite succeeded.
- Latest tested source/template checkpoint is `817f9bfc30d62c14b3f6e3ab81b56c180573b1f5`, passed in CI run [#205](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40183594878): 115 passed, 10 warnings, including CloudFormation lint for the explicit Lambda `LoggingConfig` route. Any branch commits after that test are documentation-only. `ImageUri` has no old-image default; deploying requires the immutable tag from a successful manual ECR build run on the final branch head.
- Staging migration `management_access_requests` is applied to `wxulxcsdpwsyhtpkbazi`, recorded as `management_access_requests` version `20261024191143`. Verified: RLS enabled, no `anon`/`authenticated` SELECT on the table, no `anon`/`authenticated` EXECUTE for `review_management_access_request`, service_role has the intended backend privileges, and request count is zero.
- The staging signup flow asks Employee vs Management. New profiles remain Employee by default. A verified email listed in the isolated staging Lambda parameter `ManagementEmailAllowlist` can receive Management application privileges; otherwise a Management selection queues an approval request. `public.profiles.role` remains authoritative for backend authorization.
- Current Vercel Preview environment variables were inspected read-only and are branch-specific for Cognito, staging Supabase, `/auth/callback`, `/login`, and the staging API/link URL. The latest Ready Preview we could verify has the role-selection UI, but current Lambda image/environment and a real browser E2E are not verified.
- Still not done: no current ECR image build was triggered, no CloudFormation update was made, no S3 bucket was created, and no Production service/configuration was changed. The manual ECR workflow plus update of the existing isolated staging stack (or create only if absence is confirmed) remains the release gate. Set `ManagementEmailAllowlist` only to the intended verified initial-manager email and preserve the existing staging Supabase secret through CloudFormation `NoEcho`/previous-value flow.


## Continuation checkpoint — auth-client isolation fix verified in CI (25 October 2026, 20:20 IST)

### Repository truth checked in this session
- Repository: `divyanshsaxena2209/enterprise-workplace-assistant`.
- Working branch: `cognito-staging-integration`; PR #3 remains open and draft, targeting `aws-service-replacements`.
- Branch head verified through PR #3 and the latest workflow: `e3fb038ba4846d58add5d2a84b9decdb551c058d`.
- Latest fully green CI run [#40192528581](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40192528581) passed on runtime/source SHA `e3fb038ba4846d58add5d2a84b9decdb551c058d`: **116 tests passed, 10 warnings**, plus the frontend build, backend compilation, Cognito trigger tests and CloudFormation lint. This was followed by a documentation-only handoff commit `5f660494e17080b2fae0fb4432fc8c443f33bb28`; no CI run for that documentation-only commit was listed when inspected. Check the exact latest branch head before building.
- Earlier iterations of this fix failed; do not use their results as current status. The final run above is green.
- The auth isolation test is included in CI via the existing test set/workflow, but there is no separate file named `test_auth_service_client_isolation.py` at the branch head; avoid citing that guessed filename. The behavior is implemented in source and CI is green.

### Confirmed code changes at branch head
- `backend/app/db/supabase.py` adds `create_supabase_auth_client()`, separate from the cached privileged `get_supabase_client()`.
- `backend/app/services/auth_service.py` sends session-mutating signup/login/logout through `self._auth` while profile repository reads/writes use the separately provided privileged database client.
- The candidate-provisioning isolation fix is represented in the branch's tested change set; the final CI run includes backend compilation and the selected regression suite.
- `backend/check_db.py` now requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from environment variables; it does not hard-code the credential or print profile PII.
- The repository default branch `main` still has the old shared-client implementation. Do not describe the fix as merged or available in `main`.

### Signup error and remaining release gates
- Staging evidence recorded above in this handoff identifies signup succeeding in Supabase Auth followed by profile upsert receiving 403 / `permission denied for table profiles`. The privilege checks said `service_role` already had SELECT/INSERT/UPDATE; regular client roles did not. Do not weaken RLS/table grants to bypass the issue.
- Source + CI fix are complete for this task, but deployment is **not yet verified**. The last recorded running staging image is `cognito-staging-01a284551c7fdfe6c8bf3f53f8995d12b5553cd8`, which predates the branch head `e3fb038`. It must not be treated as containing this fix.
- Safe next step is a manual build from the exact current branch head using [Build Cognito staging backend image to Amazon ECR](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml). The expected immutable tag pattern is `cognito-staging-e3fb038ba4846d58add5d2a84b9decdb551c058d`; use the tag actually emitted by the successful run, not this expectation alone.
- Then create a **new** change set for the already-existing `ewa-cognito-staging-api` stack in `ap-south-1`, changing only the image URI. Preserve both staging Supabase secret parameters with the console's previous-value / NoEcho mechanism. Retain staging demo role selection only for this isolated stack, `StorageProvider=supabase`, and blank `DocumentBucketName`. Review that `StagingApi` is in-place modify with `Replacement=False` before execution; don't reuse any stale/failed change set.
- After update completes, verify deployed image URI/digest, `/health`, then test signup with a fresh unique email, confirm profile creation and returned session, test login, and inspect the correlated sanitized CloudWatch invocation. A prior failed signup might have left an Auth identity without a profile.
- Keep PR #3 draft; do not change Production, loosen database permissions, or provision a new stack/resource for this checkpoint.
- Security follow-up remains: rotate the old-project Supabase service-role JWT if it is still active because a hard-coded value existed in Git history. Never put the key in chat or reuse it for staging.


## Standing execution rules for every continuation chat

### ChatGPT owns routine GitHub, Vercel, and Supabase work
- ChatGPT should perform all feasible repository/GitHub, Vercel, and Supabase investigation and implementation directly using the connected tools: inspect code/configuration/logs, edit files, create commits/branches/PRs when appropriate, run or inspect CI/builds, review deployment status, query Supabase metadata/logs, and apply safe database/configuration changes when authorized by the existing project scope.
- Do not ask the user to do work that ChatGPT can perform through the connected tools. Do not stop merely to ask permission for ordinary, reversible repository edits or routine verification within the existing staging/development scope.
- Inspect the available connector capabilities and use them; if a particular action is not supported or lacks authorization, state that precise limitation and choose the safest useful alternative. Never claim an action was completed unless tool results verify it.
- Preserve the existing safety boundaries: Production must remain untouched unless the user explicitly changes that instruction. Avoid destructive changes, secret disclosure, broad permission grants, and unnecessary resource creation. For sensitive/high-impact changes, review the scope and consequences before acting.

### Ask the user only for AWS-console actions or real-world/manual tests
- The expected reason to pause and ask the user to act is when a step genuinely requires their AWS console/credential/approval access, or when a live browser/device/manual test must be performed by them and ChatGPT cannot execute it with available tools.
- Before asking, exhaust safe GitHub/Vercel/Supabase-side investigation and automation. Ask for one precise action at a time, explain exactly where to go and what to do, and specify the evidence/result to report back. Do not ask the user to perform Git, Vercel, or Supabase work that connected tools can handle.
- Continue independently after receiving the requested result. Do not treat a deployment as verified until the running environment and its behavior have actually been checked.

### Minimal, high-information testing strategy
- Keep tests lean and targeted. Prefer a small number of high-value regression tests that distinguish the plausible root causes, cover the changed behavior/security boundary, and fail clearly if the bug returns.
- First inspect existing test coverage, CI configuration, logs, and related call paths; infer what can be established from those sources before adding new tests. Reuse existing fixtures and tests rather than duplicating coverage.
- Prefer one focused regression test plus existing relevant checks over many overlapping tests. Run the narrowest relevant test first, then a broader suite only when risk, dependencies, or CI requirements justify it.
- Combine related assertions where that improves signal without making failures ambiguous. Avoid redundant test cases, repeated exploratory runs, and expensive full-suite runs after a narrowly scoped change unless necessary.
- Do not sacrifice meaningful security, data-integrity, or critical-flow coverage just to reduce test count. Record exactly which checks ran, what passed/failed, and what remains unverified; never imply that a test passed if it was not run.


## Fast-demo checkpoint — current image built, CI green, AWS update is the only blocker (25 October 2026)

### Verified in this continuation
- Current source branch at this checkpoint: `cognito-staging-integration`, commit `c9479602cc402971429bd9461d8c7f59d9d62bb8`.
- [Staging ECR build run #19](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40204959894) completed successfully. The immutable image and registry manifest digest are:
  - Image tag URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-c9479602cc402971429bd9461d8c7f59d9d62bb8`
  - Preferred immutable digest URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend@sha256:63d92ca62b227d2e8dd340500e19e17b448de7952dcf5a6f0820d07ad3f3158b`
  - Image configuration digest: `sha256:92dbcecc6b71539b9a188e01b34827a4f74035cfed7df3f784ee6b9e7faf852d`
- [CI run #215](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40204959854) completed successfully on the same SHA: **116 passed, 10 warnings**. The pre-token-generation trigger tests, Vercel frontend build, backend/test compilation, CloudFormation lint and the targeted regression tests passed. The auth-session/client-separation regression is in `backend/tests/test_cognito_provisioning_errors.py` (not a separate `test_auth_service_client_isolation.py` file).
- The staging-only ECR workflow now runs automatically on pushes to `cognito-staging-integration` when `backend/**` or the ECR workflow file changes; manual dispatch is still available. It never triggers on `main` or another branch through this new push trigger.
- Vercel reports the Preview deployment for commit `c9479602cc402971429bd9461d8c7f59d9d62bb8` is READY. Its URL at the time of this check was `https://enterprise-workplace-assistant-mk2fiqoue-divyansh-50b7.vercel.app`. Vercel's deployment fetch/runtime log API returned 403 for this integration, so the page and login flow have not been independently tested through the connector.
- Supabase project `wxulxcsdpwsyhtpkbazi` (`workplace-assistant-staging`) is `ACTIVE_HEALTHY`. Read-only SQL confirms `service_role` has SELECT/INSERT/UPDATE for `public.profiles`, `authenticated` cannot INSERT profiles, and there are currently **0 auth users without a profile**. Do not change grants or reset database data to address the old 403.

### Exact next step — the user must do this in AWS Console
The connected GitHub/Vercel/Supabase tools cannot update or inspect the live CloudFormation stack. Do **not** create a second stack or touch Production.

1. Open AWS Console → CloudFormation, region **Asia Pacific (Mumbai), `ap-south-1`**. Select the existing `ewa-cognito-staging-api` stack only. Confirm its status permits an update. If the stack is in a failed/rollback state, stop and share only the stack status and latest event failure reason (no secrets).
2. Create a **new change set** using the current branch template `infra/aws/cognito-staging-backend.yml` from this branch. Set `ImageUri` to the immutable digest URI above. Preserve `SupabaseServiceRoleKey` and `SupabaseJwtSecret` using the console's **Use previous value**/NoEcho handling; never reveal either secret. Keep `DemoRoleSelectionEnabled=true` for the isolated staging demo, `StorageProvider=supabase`, `DocumentBucketName` blank, and leave `ManagementEmailAllowlist` blank in demo-selector mode unless an allowlisted initial manager is specifically required.
3. Inspect the change set before execution. Continue only if the expected change is the existing `StagingApi` being modified in place (`Replacement=False`) with no unexpected new resources, deletions, Production resources or cost-bearing services. If the change set says replacement or lists unexpected resources, do not execute it; send the resource/action summary.
4. Execute the reviewed change set, then wait for `UPDATE_COMPLETE`. Confirm the Lambda image uses the digest above. Do not paste credentials into chat.

### Minimum live acceptance after deployment
Use the staging Preview URL only. Perform one consolidated test:
- Open `/login`, select Employee and complete Cognito sign-in/signup through `/auth/callback`.
- Verify the API returns a successful session and a profile exists for the new staging identity; then sign out and sign in again.
- Use the Management option and verify the current staging-demo role behavior. Confirm a role-restricted API call is allowed/denied as expected.
- Confirm the same invocation produces a CloudWatch event in `/aws/lambda/ewa-cognito-staging-api` (7-day retention), without tokens or secrets in logs.
- Report observed status/results only. If any one step fails, capture the exact error/status and timestamp so we can correlate it without repeating multiple test runs.

### Current truth
- Source fix: implemented.
- Automated CI: passed (116 tests, 10 warnings).
- Staging ECR image: built and pushed with digest above.
- Vercel branch Preview: READY.
- Supabase profile grants/data consistency check: passed.
- Lambda update, live Cognito browser sign-in/profile verification, application role acceptance and fresh CloudWatch log correlation: **not yet verified**.
- PR #3 stays draft; Production remains untouched; S3 remains out of scope for this four-service demo checkpoint.


## Follow-up after user reports CloudFormation UPDATE_COMPLETE — deployed image still needs refresh

### New evidence discovered after the screenshot
- User screenshot confirms the existing `ewa-cognito-staging-api` stack reached `UPDATE_COMPLETE` at **2026-10-25 17:08:54 IST**. This proves the CloudFormation operation completed, but the screenshot does not show the deployed `ImageUri`.
- Supabase staging logs show a subsequent email signup at **2026-10-25 17:39:46 IST** returned Auth `200`, followed by a profile upsert returning `403`. In the corresponding PostgREST log, the API key role was `service_role` but the Authorization JWT role was `authenticated`; PostgreSQL then reported `permission denied for table profiles`. This is the precise shared/session-contamination signature the code fix is meant to prevent.
- Therefore, do **not** assume the earlier stack update has proved the fix. The failing request occurred before the current image build below and indicates the running path at that time still sent the user JWT on the profile upsert. It may have used a stale image (the screenshot alone cannot prove its image tag).
- Staging DB privileges remain correct: service_role has SELECT/INSERT/UPDATE on `public.profiles`; authenticated cannot INSERT; there were 0 Auth users without profiles at the read-only health check. Do not widen grants.

### Fresh image now available — needs a second in-place update
- After the above error timestamp, CI run #19 built and pushed the branch-head backend image successfully: [run #19](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40204959894).
- Current image tag: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-c9479602cc402971429bd9461d8c7f59d9d62bb8`.
- Current image digest URI: `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend@sha256:63d92ca62b227d2e8dd340500e19e17b448de7952dcf5a6f0820d07ad3f3158b`.
- The same commit's CI run #215 passed: **116 tests, 10 warnings**, including frontend build, backend compile, CloudFormation lint and focused regression suite: [run #215](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/40204959854).
- Required next step remains a second change set on the existing staging stack only, updating `ImageUri` to the immutable digest above. Preserve staging secret parameters using previous-value/NoEcho handling. Before execution verify the existing `StagingApi` is changed in place (`Replacement=False`) and no unexpected resources are added/deleted. Production untouched.
- After `UPDATE_COMPLETE`, perform exactly one fresh test through the currently READY Vercel Preview. Correlate its timestamp with the staging logs. Success criteria are: Auth signup returns 200; following `POST /rest/v1/profiles?on_conflict=id` has Authorization role `service_role` (not `authenticated`) and returns success; the profile exists; then login succeeds. If it still fails, capture the exact time and response/error—do not repeat signups or relax grants.
- Current Vercel runtime-log/fetch connector access returned HTTP 403, so live end-to-end validation must be done through the preview/browser and AWS CloudWatch until connector access is fixed.
