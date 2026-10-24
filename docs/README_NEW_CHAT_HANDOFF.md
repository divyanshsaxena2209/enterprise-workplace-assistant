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
