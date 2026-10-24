# Enterprise Workplace Assistant — AWS Migration Handoff

Updated: 2026-10-25
Repository: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant
Working branch: `migration/security-hardening-jwt-rbac`

## Current verified state

The current repository default branch is `main`. The most recent relevant commits (through 2026-10-21) added a Python Lambda Runtime Interface Client + Mangum entry point, Lambda Function URL-oriented CORS behavior, and two GitHub Actions ECR image workflows. The application is not yet fully migrated from Supabase-managed services to AWS.

### Requirements and status

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| GitHub Actions to AWS through OIDC | Partially implemented | `.github/workflows/build-backend-ecr.yml` assumes `GitHubActions-EWA-Deploy` in account `745531385877`, region `ap-south-1`. Verify trust policy, exact repository/branch conditions and least-privilege permissions in AWS. |
| Isolated Cognito staging backend image | Pipeline configured; deployment not verified | `.github/workflows/build-cognito-staging-ecr.yml` assumes `GitHubActions-EWA-Cognito-Staging-ECR`. Workflow only builds/pushes a tagged image; it does not create or update Cognito, Lambda, Function URL, or frontend callback settings. |
| Amazon Cognito sign-up/sign-in | Not migrated | `backend/app/routers/auth.py` delegates to the existing `AuthService` backed by Supabase Auth. Need an isolated staging user pool/app client, callback/logout URLs, frontend integration, JWT/JWKS verification, profile/role mapping and end-to-end tests. |
| Lambda backend | Code entry point configured; deployed behavior unverified | `backend/app/lambda_handler.py`, Dockerfile Runtime Interface Client entry point and ECR workflow exist. Verify image build, Lambda architecture/memory/timeout/temp storage, environment variables, Function URL auth/CORS, cold start and smoke tests. |
| S3 resume uploads and downloads | Not migrated | `backend/app/routers/resume.py` still uploads into Supabase Storage bucket `resumes` and stores a public URL. `backend/app/routers/hiring.py` downloads from that same Supabase bucket. Migration must update upload, persisted object reference, authorized download/screening, delete/retention and compatibility for old URLs together. Use private S3 objects and short-lived presigned URLs or server-side reads. |
| S3 knowledge/policy documents | Not migrated | `backend/app/routers/knowledge.py` saves knowledge files to the same Supabase `resumes` bucket and returns a public URL, while chunks are indexed in Qdrant. Introduce a separate private bucket prefix (for example `knowledge/`) and keep indexing metadata tied to stable object keys. Coordinate delete from S3 and Qdrant. |
| IAM application roles | Not evidenced in repo | Keep the Lambda execution role separate from GitHub Actions image-publishing roles. Runtime role should only have the required S3 prefixes and CloudWatch Logs permissions; no broad S3 admin access. |
| Employee vs management access control | Critical issues found; remediation started on branch | JWT verification was explicitly disabled, and a magic bearer token `guest` granted MANAGEMENT role. Knowledge upload/delete lacked role dependencies. Changes on `migration/security-hardening-jwt-rbac` require CI/review and role-specific tests before merge. |
| CloudWatch monitoring | Not evidenced in repo | Verify Lambda log group, retention policy, alarms for errors/throttles/duration and basic dashboard/alerts. Avoid high-cardinality or secret-bearing logs. |
| Frontend hosting / API configuration | Partial / unverified | Repo uses Next.js and local environment configuration. Confirm deployed frontend API base URL, Cognito hosted UI callback/logout URLs, CORS origin and HTTPS before staging validation. |

## Security findings

1. `backend/app/core/security.py` used PyJWT with `verify_signature=False` even when a secret was configured. The branch now requires an `SUPABASE_JWT_SECRET` and validates HS256 signatures and expiry. This is an interim hardening for the current Supabase JWT flow, not the final Cognito JWT solution. Cognito tokens normally require issuer/audience checks and signature validation with the user pool JWKS; implement that before switching the frontend to Cognito.
2. `backend/app/dependencies/auth.py` and `backend/app/middleware/auth_middleware.py` accepted a hard-coded `Bearer guest` and fabricated a Management profile. Removed on the working branch; tests/development bypasses should use dependency overrides, not magic bearer tokens.
3. `backend/app/routers/knowledge.py` allowed unauthenticated document upload/delete at the route level despite other chat operations requiring authenticated users. The branch changes upload and delete to require Management and sanitizes temporary upload names / limits file size.
4. `backend/app/middleware/auth_middleware.py` logged all request headers on `POST /api/v1/jobs`, potentially including authorization credentials. That logging was removed on the branch.
5. Resume and knowledge-document storage currently expose public URLs. Do not repeat that pattern with S3. Use private objects, scoped permissions, content type/size validation, safe object keys and controlled downloads.

## Changes made on `migration/security-hardening-jwt-rbac`

- Require verified HS256 JWT signatures and expiration; fail closed when the configured secret is missing.
- Remove the magic Management guest token from dependency and middleware paths.
- Remove request-header logging from auth middleware.
- Restrict knowledge document upload/delete to the Management role; constrain allowed file extensions/content types and size, use generated temporary names, avoid returning raw exception text, and make storage failure visible.
- Add `backend/tests/test_auth_security.py` regression tests for missing secret, invalid signature, expiry and valid signature.

These changes are committed directly to the working branch and have not been merged to `main`. They have not been executed in a local test environment by this GitHub connector; CI/test results must be checked before merge.

## Next execution sequence

1. Validate this branch using GitHub Actions or a local environment. Resolve any failing tests; add role tests proving employees cannot upload/delete knowledge documents while Management can.
2. Add Cognito token validation behind an explicit auth-provider configuration and test it against a dedicated staging user pool. Do not silently accept both unverified Supabase and Cognito JWTs.
3. Implement an S3 storage abstraction with separate private prefixes/buckets for resumes and knowledge documents. Add server-side download and short-lived presigned URL paths; update resume screening, file deletion, metadata and legacy Supabase URL compatibility.
4. Define minimal IAM policies: Lambda execution role (S3 object access only to named buckets/prefixes, CloudWatch Logs), separate GitHub OIDC ECR-push roles, and no production access from staging.
5. Complete staging deploy configuration and verify Lambda URL auth/CORS, Cognito callback/logout URLs, frontend API URL and employee/management workflows.
6. Add CloudWatch log retention, error/throttle alarms and smoke-test checklist.
7. Update operational documentation and only then plan any production cutover.

## Cost and safety guardrails

- No AWS resources were created or modified during this work.
- Do not run the ECR workflow or deploy/update Lambda merely to test source edits; ECR pushes, image storage, Lambda and logs can incur cost.
- Keep Cognito validation isolated to staging and do not alter Production callback URLs, buckets, IAM policies or running services until staging tests pass.
- Do not print secrets, raw authorization headers, presigned URLs, resume contents, or private document links in logs.
