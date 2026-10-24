# AWS Migration Handoff — Enterprise Workplace Assistant

Updated: 2026-10-25
Repository: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant
Working branch: `migration/security-hardening-jwt-rbac`
Draft PR: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/pull/4

## Summary

The migration is partially implemented, not complete. The current `main` branch has a Lambda Python runtime entry point, a Lambda Runtime Interface Client Docker entry point, and GitHub Actions workflows to build/push backend images to ECR. It does not prove Cognito is integrated, private S3 storage is used by application routes, or CloudWatch alarms/retention are configured.

## Requirement / progress matrix

| Requirement | Current state | Next action |
|---|---|---|
| GitHub Actions OIDC to AWS | Partially configured | Verify the trust policy for `GitHubActions-EWA-Deploy` and `GitHubActions-EWA-Cognito-Staging-ECR` only trusts this repository and intended branch/ref. Verify ECR-only permissions for build roles. |
| Lambda backend | Runtime entry point configured; deployed health unverified | Verify the staged image builds, environment variables are configured, Function URL CORS/auth matches intended public/private endpoints, and /health smoke test succeeds. |
| Amazon Cognito | Not migrated | Create/verify an isolated staging User Pool and app client, callback/logout URLs, frontend sign-in/sign-up, backend JWT validation against user-pool JWKS, profile and MANAGMENT/EMPLOYEE role mapping. Do not accept Cognito tokens using the Supabase HS256 verifier. |
| Resume S3 storage | Not migrated | `backend/app/routers/resume.py` still uploads to Supabase Storage `resumes` and persists a public URL. `backend/app/routers/hiring.py` downloads from that bucket. Add private S3 object keys, upload and authorized read/download, screening integration, deletion, legacy URL compatibility and tests together. |
| Knowledge/policy document S3 storage | Not migrated | `backend/app/routers/knowledge.py` still stores source documents in the Supabase `resumes` bucket while indexing chunks in Qdrant. Add separate private `knowledge/` object prefix or dedicated bucket; coordinate object metadata, Qdrant chunk source metadata and deletion. |
| IAM app roles | Not evidenced in repo | Separate Lambda execution role from GitHub OIDC ECR publishing roles. Give runtime role least privilege to specific S3 prefixes and CloudWatch Logs; prohibit staging from modifying production. |
| CloudWatch | Not evidenced in repo | Configure log retention, error/throttle/duration alarms and a basic operational dashboard. Avoid log leakage of auth headers, resume text and private URLs. |
| Employee vs Management access | Severe issues found; partial remediation on branch | Require CI and route-level RBAC tests. Upload/delete of knowledge documents must remain Management-only; chat/session endpoints must enforce session ownership. |
| Docs and operational readiness | New handoff added on branch | Keep the status matrix updated after each migration PR; record staging test results and explicitly note what remains unverified. |

## Security findings and branch work

Before the branch changes, the application disabled PyJWT signature verification even when `SUPABASE_JWT_SECRET` was set; a hard-coded `Bearer guest` token was converted into a fabricated Management user; auth middleware logged all headers on one jobs route; and knowledge upload/delete had no Management dependency.

On `migration/security-hardening-jwt-rbac`:
- Require Supabase HS256 signature and expiration verification and fail closed if the secret is absent.
- Remove the magic guest Management bypass from dependencies and middleware.
- Remove authorization-header logging.
- Require Management role for knowledge document upload and deletion, limit upload types/size, generate temporary filenames server-side and avoid returning raw exception details.
- Validate session ownership before saving a chat query message, clean up temporary files, and improve safe error handling.
- Add `backend/tests/test_auth_security.py` for missing secret, invalid signature, expired and valid tokens.
- Add this migration handoff.

Important caveats:
- The current auth patch is an interim fix for the existing Supabase HS256 token configuration. Cognito requires issuer/audience validation and signature verification against the User Pool JWKS, with token-use checks. Add this as a distinct, explicit auth-provider implementation before switching frontend authentication.
- No local test run was possible through the GitHub connector, and no branch workflow run was found. Treat tests as unverified until CI/local tests pass.
- The knowledge document source upload still writes to Supabase Storage. This is deliberately not described as an S3 migration.
- The repository currently has no evidence of an S3 storage abstraction, Cognito route/provider implementation, CloudWatch alarms, or verified AWS service configuration.

## Next sequence

1. Run all backend tests and lint/import checks. Add route-level RBAC tests that prove an EMPLOYEE cannot upload/delete knowledge documents and MANAGEMENT can; add session-ownership tests.
2. Add Cognito validation separately from Supabase token validation. Use JWKS verification with issuer, audience/client and token-use checks, then stage sign-up/sign-in and profile role mapping.
3. Implement one storage abstraction that supports stable private object keys. Migrate resume upload + screening/read/delete together and knowledge document upload + Qdrant indexing + delete together. Prefer server-side reads or short-lived presigned URLs; never expose public S3 URLs.
4. Document and implement least-privilege IAM policies. Keep Lambda execution, GitHub ECR-publish, and staging roles separate.
5. Verify staging ECR image, Lambda Function URL, CORS, Cognito callbacks, frontend API URL, health and employee/management flows.
6. Add CloudWatch log retention and actionable alarms; run smoke tests.
7. Reconcile data migration/legacy Supabase object references and decide a tested cutover/rollback plan before Production.

## Cost and deployment guardrails

- This work has not created or modified any AWS resource.
- Do not trigger ECR builds/deployments simply to validate source edits: image pushes/storage, Lambda, logs and related resources can incur cost.
- Keep all validation in isolated staging. Do not update production IAM, callbacks, buckets or live resources until staging tests pass.
- Never log secrets, Authorization headers, resume contents, or private/presigned object URLs.
