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
| Lambda access to AWS resources | Lambda execution IAM role, least privilege | S3 policy still needs to be attached to the existing Lambda execution role; app business roles are enforced by FastAPI |
| User authentication | Amazon Cognito User Pool | Not migrated |
| File/object storage | Private Amazon S3 bucket | S3 provider staged for chatbot knowledge-document files and resume files; Supabase remains default until bucket and IAM permissions are configured. Job listing text stays in the relational database because the current job schema has no file-attachment upload |
| Relational application database | Amazon RDS for PostgreSQL (assumed missing item) | Not migrated; current backend uses Supabase PostgREST/client and has relational schema |
| Monitoring and alerts | CloudWatch Logs, log retention, metrics/alarms | Lambda logs use CloudWatch by default; retention and alarms need final setup |
| AI and vector search | Gemini + Qdrant Cloud | Keep unchanged |
| Frontend | Vercel | Keep unchanged |

## Implementation staged on branch `aws-service-replacements`

- Added `STORAGE_PROVIDER`, `AWS_REGION`, `AWS_S3_BUCKET`, and presigned-URL lifetime settings. The default provider remains `supabase`, so existing production configuration is unchanged.
- Added an object-storage provider using the Lambda execution role's default AWS credential chain (no AWS access keys), SSE-S3 encryption, private object keys under `knowledge/` and `resumes/`, and short-lived presigned GET URLs.
- Updated knowledge-document upload/delete/view flow and resume upload/detail flow to use S3 when `STORAGE_PROVIDER=s3`.
- Added tests for S3 object prefixes, encryption, deletion guards, presigned URL scope, and manager/employee/guest role permissions. The isolated storage + RBAC tests passed in [GitHub Actions](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39587229252); a full backend syntax-compile step has now been added and is running.
- Manager/employee enforcement is staged: management-only job mutations, candidate/recruiter/evaluation visibility, knowledge upload/delete, and employee-scoped applications/onboarding; public signup cannot self-assign Management; guest mode is no longer a manager and cannot use write guards.
- Chatbot file bytes are designed for S3 under `knowledge/`; resume bytes under `resumes/`. The chatbot's indexed chunks remain in Qdrant, resume/application records remain in the relational database, and job listing fields remain in the relational database. The job schema does not currently support uploaded JD attachments.
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
