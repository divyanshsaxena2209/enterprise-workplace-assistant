# AWS Service Replacement Plan

## Production baseline

The production application currently uses:
- Vercel for the Next.js frontend.
- AWS Lambda Function URL + an Amazon ECR container image for the FastAPI backend.
- Supabase Auth and Supabase PostgreSQL for users/profiles and application data.
- Supabase Storage for some knowledge-document uploads.
- Gemini for AI and Qdrant Cloud for vector search.

Do not remove Supabase, Gemini, Qdrant, Lambda, or ECR until each replacement is validated in production.

## Target service map

| Responsibility | Target | Status |
|---|---|---|
| Backend hosting | AWS Lambda + ECR | Deployed and smoke-tested |
| CI/CD AWS access | GitHub Actions OIDC -> IAM role | Build/push role already configured; Lambda auto-update still needs verification |
| Lambda access to AWS resources | Lambda execution IAM role, least privilege | Existing execution role; add only permissions required by each cutover |
| User authentication | Amazon Cognito User Pool | Not migrated |
| File/object storage | Private Amazon S3 bucket | S3 provider implementation staged on this branch for knowledge documents and resumes; Supabase remains the default until bucket and IAM permissions are configured |
| Relational application database | Amazon RDS for PostgreSQL (assumed missing item) | Not migrated; current backend uses Supabase PostgREST/client and has relational schema |
| Monitoring and alerts | CloudWatch Logs, log retention, metrics/alarms | Lambda logs use CloudWatch by default; retention and alarms need final setup |
| AI and vector search | Gemini + Qdrant Cloud | Keep unchanged |
| Frontend | Vercel | Keep unchanged |

## Implementation staged on branch `aws-service-replacements`

- Added `STORAGE_PROVIDER`, `AWS_REGION`, `AWS_S3_BUCKET`, and presigned-URL lifetime settings. The default provider remains `supabase`, so existing production configuration is unchanged.
- Added an object-storage provider using the Lambda execution role's default AWS credential chain (no AWS access keys), SSE-S3 encryption, private object keys under `knowledge/` and `resumes/`, and short-lived presigned GET URLs.
- Updated knowledge-document upload/delete/view flow and resume upload/detail flow to use S3 when `STORAGE_PROVIDER=s3`.
- Added unit tests for S3 object prefixes, encryption, deletes, and presigned URL scope. The isolated GitHub Actions test workflow passed on commit `ef124a681d8af3ff5e2f4855847280be6c2a6543`.
- This branch has not been merged or deployed. The S3 bucket and Lambda IAM policy are not yet created. Existing Supabase files/data have not been bulk-migrated to S3.

## Safe migration order

1. Preserve the working production app; implement replacements on this branch first.
2. Keep static AWS keys out of the app. Lambda should use its execution role; GitHub Actions should assume the existing OIDC deployment role.
3. Create and test Cognito while keeping Supabase users/data available for rollback. Decide user migration before cutover: Cognito supports a migration trigger for users who authenticate for the first time, or bulk import that may require users to reset passwords.
4. Create a private S3 bucket with Block Public Access and default encryption. Grant the Lambda execution role only the required object actions on that bucket. Use presigned URLs for temporary browser downloads instead of making documents public.
5. Migrate the PostgreSQL schema and data to RDS only after confirming the networking and cost model. RDS is not a drop-in replacement for the Supabase HTTP client: repository/data access and frontend direct Supabase data queries must be migrated. Lambda-to-RDS networking may also affect outbound access to Gemini/Qdrant; avoid creating a NAT Gateway without explicitly reviewing cost.
6. Add CloudWatch log retention and practical error/latency alarms after the cutover is stable.
7. Run the full smoke test (signup/sign-in, profile/role, job CRUD, applications/candidates, onboarding, knowledge upload/query) before switching traffic. Keep a rollback path until it passes.

## Guardrails

- Never commit secrets, Supabase service-role keys, Cognito secrets, or AWS access keys.
- Do not delete existing Supabase Auth/database/storage data while the app still depends on it.
- Do not use a public S3 bucket for resumes or company documents.
- Do not create RDS/NAT resources without checking the account's credit/billing status and expected monthly charges.
- Keep the production main branch unchanged until each feature on this migration branch is tested.
