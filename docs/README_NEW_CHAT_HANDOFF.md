# Enterprise Workplace Assistant — Migration Continuation Handoff

**Purpose:** Current source of truth to paste into a new ChatGPT conversation. Verify live branch/resource state before making changes. This replaces the older October 21 snapshot where it conflicts with this document.

**Snapshot:** 22 October 2026 (Asia/Kolkata)  
**Repository:** https://github.com/divyanshsaxena2209/enterprise-workplace-assistant  
**Working branch:** cognito-staging-integration  
**Draft PR:** https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/3  
**PR base:** aws-service-replacements  
**Code head verified for this snapshot:** b3be0587d1bf910e2fe0086ac1be35266349e46b  
**Latest passing CI for that code head:** run #84 — https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39723988185  

Keep PR #3 in draft. The handoff-documentation commit may advance the branch SHA; check the current SHA before any build or deployment. Do not merge into main before real staging end-to-end tests pass.

---

## 1. Project aim and modules

Enterprise Workplace Assistant is a workforce-operations and hiring platform with:
- Employee/management profiles and role-based access control.
- Job listing and publishing, candidate tracking, applications, resume screening, evaluations, recruiter notes and interview workflows.
- Employee onboarding templates, assigned tasks, progress tracking and management oversight.
- Company knowledge-document uploads, retrieval and department-sensitive RAG/chatbot features.
- Separate management and employee dashboards.

The frontend is Next.js App Router. The backend is FastAPI. The relational schema is PostgreSQL accessed through Supabase/PostgREST. Gemini powers LLM features and Qdrant Cloud supplies vector retrieval. These are the existing services to preserve while introducing Cognito and, later, private S3 storage.

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
- Leave Supabase Auth and Supabase Storage as defaults until the Cognito/S3 integrations have passed staging checks and a rollback plan exists.

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
