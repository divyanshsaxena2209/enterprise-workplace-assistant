# Enterprise Workplace Assistant — AWS Deployment & Service-Replacement Handoff

> **Purpose:** Paste this README into a fresh ChatGPT conversation so work can continue without reconstructing the deployment history.
>
> **Snapshot date:** 21 October 2026  
> **GitHub repository:** https://github.com/divyanshsaxena2209/enterprise-workplace-assistant  
> **Working branch:** `aws-service-replacements`  
> **Branch snapshot when this note was written:** `456044ce2486d5caec554ee0361f8a5b472e62d4`  
> **Important:** The production `main` branch has NOT been changed by these service-replacement edits. Do not merge or deploy the replacement branch until the integration review, role tests, S3 setup and smoke tests are complete.

## 1. What the user wants

Complete the AWS deployment and staged service replacements for the Enterprise Workplace Assistant. The application is a workforce / hiring portal with job listings, candidate applications and resume screening, a chatbot/knowledge base, and employee onboarding.

User preferences and constraints:
- Give direct, actionable steps in larger chunks rather than dozens of tiny checks.
- The user works in the AWS Console manually and uses Windows/PowerShell when commands are needed.
- For AWS Console instructions, provide ordinary hyperlinks and numbered steps; do not use button-like links.
- Prioritize low cost. Avoid creating cost-prone resources (especially RDS, NAT Gateway, EC2, reserved capacity) until need and monthly cost have been discussed. An AWS billing dashboard screenshot showed no cost data yet; that is not proof that usage is free.
- Do not change the working production deployment casually. Use the isolated branch first.
- Preserve Gemini and Qdrant Cloud unless the user explicitly asks to replace them.
- Do not ask the user to paste credentials, API keys, JWT secrets, or other secrets into chat.

## 2. Current production architecture and known-good deployment

| Area | Current state |
|---|---|
| Frontend | Vercel: https://enterprise-workplace-assistant.vercel.app |
| Backend | FastAPI container hosted by AWS Lambda |
| Lambda function | `enterprise-workplace-assistant-api` |
| AWS region | `ap-south-1` (Mumbai) |
| Lambda Function URL | `https://6wdbue2ejwqbs2pqtro4u7ojei0bxrcp.lambda-url.ap-south-1.on.aws/` |
| Container image | Amazon ECR repository `enterprise-workplace-assistant-backend`, tag `latest` |
| Application auth | Supabase Auth, Supabase JWTs and profile table |
| Relational database | Supabase PostgreSQL/PostgREST |
| Existing object storage | Supabase Storage bucket used by upload flows (not yet retired) |
| AI | Gemini |
| Vector database | Qdrant Cloud |
| Monitoring | Lambda logs are available in CloudWatch; retention/alarms remain to be finalized |
| Frontend hosting | Keep Vercel; not migrating it to AWS |

Production smoke tests were observed working on 21 Oct 2026: the health endpoint returned `{"status":"ok","version":"1.0.0","environment":"development"}` (note the environment label still says development), login worked with the existing Supabase credentials, job listings/details loaded, and candidate records were visible to a management account. During troubleshooting, the backend briefly had CORS errors; the Function URL CORS was configured for the Vercel origin. The Function URL has Auth type `NONE`, so it is reachable publicly; route-level authentication/authorization must remain correct. Never treat CORS as an authentication mechanism.

The Lambda uses a container image with AWS Lambda Web Adapter. Lambda container updates require an explicit Lambda image update after pushing an image to ECR; pushing a new image tagged `latest` does **not** automatically change the digest used by the existing function. See AWS docs: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

## 3. AWS deployment history and current resources

- The initial AWS CodeBuild attempt failed repeatedly with `Cannot have more than 0 builds in queue for the account`. A quota increase/support case was opened, but the user ultimately successfully built and pushed the image using GitHub Actions.
- The GitHub Actions workflow is `.github/workflows/build-backend-ecr.yml` on the default branch.
- GitHub Actions uses OIDC to assume the IAM role `GitHubActions-EWA-Deploy`. Keep this role: it is part of the container-build/push workflow.
- The ECR repository is `enterprise-workplace-assistant-backend`.
- The Lambda function is `enterprise-workplace-assistant-api` in Mumbai.
- A Lambda Function URL was created with Auth type `NONE`; CORS was set to allow the deployed Vercel origin and application methods/headers.
- An initial health check returned an internal error caused by a read-only filesystem write. The application was updated to use `/tmp`, then `/health` returned OK.
- The temporary EC2 troubleshooting instance was terminated.
- Temporary CodeBuild cleanup was completed: CodeBuild project `enterprise_workplace_assistant`, S3 source bucket `ewa-codebuild-src-745531385877-ap-south-1`, and temporary role `ewa-codebuild-ecr-role` were the cleanup targets. The user reported cleanup complete.
- The successful backend ECR GitHub Actions run was run #3 (the exact URL from the conversation: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39554468500).
- Do not recreate CodeBuild or temporary EC2; they were troubleshooting paths, not part of the final deployment architecture.
- Verify current AWS state in the console rather than assuming anything changed since this snapshot.

Console links:
- Lambda (Mumbai): https://ap-south-1.console.aws.amazon.com/lambda/home?region=ap-south-1
- ECR repositories (Mumbai): https://ap-south-1.console.aws.amazon.com/ecr/repositories?region=ap-south-1
- IAM roles: https://console.aws.amazon.com/iam/home#/roles
- S3 buckets (Mumbai): https://s3.console.aws.amazon.com/s3/buckets?region=ap-south-1
- CloudWatch (Mumbai): https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1
- Billing: https://console.aws.amazon.com/billing/home

## 4. Service-replacement goal

The user specifically wants:
1. **IAM role-based permissions**: managers vs employees in the app, and AWS workload access through IAM roles.
2. **Amazon Cognito** to replace Supabase Auth.
3. **Amazon S3** for uploaded files: chatbot/knowledge documents and resumes; if actual job-description attachments are supported/added, store those too.
4. **CloudWatch** monitoring and log retention.
5. There was a possible fourth replacement discussed as **Amazon RDS for PostgreSQL** to replace the Supabase relational database, but this item was not firmly confirmed. Ask once if it is indeed the intended database replacement before committing to an RDS migration. RDS can add cost and VPC/networking complexity for Lambda outbound calls to Gemini/Qdrant.

Keep the existing database, auth, Supabase Storage, Gemini, Qdrant and production configuration until each replacement is tested. Never delete Supabase data during these cutovers.

## 5. Work already staged on `aws-service-replacements`

Branch URL: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/tree/aws-service-replacements

Docs:
- Service plan: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/aws-service-replacements/docs/aws-service-replacement-plan.md
- S3 cutover checklist: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/aws-service-replacements/docs/aws-s3-cutover-checklist.md
- Manager/employee access matrix: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/aws-service-replacements/docs/aws-role-access-matrix.md

### IAM / manager-versus-employee authorization staged in code
Files changed on the branch include:
- `backend/app/dependencies/auth.py`
- `backend/app/middleware/auth_middleware.py`
- `backend/app/services/auth_service.py`
- `backend/app/routers/applications.py`
- `backend/app/routers/candidates.py`
- `backend/app/routers/evaluations.py`
- `backend/app/routers/knowledge.py`
- `backend/app/routers/onboarding.py`
- `backend/app/routers/resume.py`
- `backend/app/routers/hiring.py`
- `frontend/app/(dashboard)/knowledge/page.tsx`

Changes staged include:
- Public signup rejects attempts to self-select `MANAGEMENT`; elevated accounts must be provisioned by a trusted admin workflow.
- The special guest/demo identity is no longer assigned `MANAGEMENT` and is blocked from management/employee write guards.
- Manager-only routes include job management (already present), candidate list/detail/delete, evaluation scores and re-evaluation, knowledge-document upload/delete, recruitment pipeline/notes, and onboarding employee creation.
- Employees can submit applications as their own authenticated identity and can access their own onboarding tasks/chat; managers can act on any employee onboarding record.
- Resume uploads require a real signed-in employee or management identity.
- Hiring/resume screening now uses the common `MANAGEMENT` role guard and includes compatibility for old Supabase resume objects versus new S3 keys.
- Knowledge upload/delete controls are hidden from employee UI, while server-side role checks enforce the restriction. Frontend hiding alone is never security.
- Existing role dependencies already used `MANAGEMENT` and `EMPLOYEE` enums. Some routes/data-access paths may still need a thorough audit; do not call the app fully secured until integration tests cover all endpoints, including the application details/scores and every onboarding route.

### S3 storage staged in code
Files changed/added include:
- `backend/app/services/object_storage.py`
- `backend/app/core/config.py`
- `backend/requirements.txt`
- `backend/app/routers/knowledge.py`
- `backend/app/routers/resume.py`
- `backend/app/repositories/candidate_repository.py`
- `backend/app/repositories/application_repository.py`
- `backend/app/routers/hiring.py`
- `frontend/lib/api/knowledge.ts`
- `frontend/app/(dashboard)/knowledge/page.tsx`

New environment settings staged:
- `STORAGE_PROVIDER=supabase` (default deliberately keeps production behavior unchanged until S3 is ready)
- `AWS_REGION=ap-south-1`
- `AWS_S3_BUCKET=` (must be the exact new bucket name before S3 mode)
- `S3_PRESIGNED_URL_TTL_SECONDS=900`

The staged S3 provider:
- Uses `boto3` and the Lambda execution role's standard AWS credential chain (no AWS access keys in env vars).
- Uploads to private prefixes `knowledge/` and `resumes/`.
- Uses SSE-S3 (`AES256`) in the upload call.
- Creates short-lived pre-signed GET URLs for authorized reads.
- Supports deletion from the correct object prefix.
- Leaves Supabase storage selected by default for rollback.
- Keeps old resume links in Supabase supported; files are not automatically bulk-copied from Supabase to S3.

### Important gap: job listing data vs job-description files
The existing job listing model contains database fields such as title, department, location, description, requirements and status. It does not currently define a job-attachment upload field or route. Therefore:
- **Job listings themselves remain relational records in the database, not S3 files.**
- Chatbot/knowledge uploaded documents are the `knowledge/` objects.
- Resume uploads are the `resumes/` objects.
- If the product must accept PDF/DOCX job description attachments, add that as a separate feature and an S3 prefix such as `job-descriptions/`, then store the object key in the job record. That feature is not yet implemented on the branch and must not be represented as done.
- If the user only means the typed job listing title/description, that continues to be saved in the DB, and S3 is not needed for it.

## 6. S3 bucket and IAM policy still need manual AWS setup

No S3 cutover should happen until the bucket and Lambda role policy exist.

Create a unique bucket name in `ap-south-1` (example placeholder: `ewa-private-documents-<unique-suffix>`; do not assume the name is available). Configure:
- Object Ownership: Bucket owner enforced.
- **Block all public access** enabled (all four settings).
- Default encryption SSE-S3.
- No public bucket policy or public ACL.
- Keep bucket private; use temporary pre-signed URLs instead of public object URLs.

Attach an inline policy to the **Lambda execution role** (the role shown at Lambda → Configuration → Permissions), not to the GitHub Actions OIDC role. Replace `YOUR_BUCKET_NAME` before saving:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageKnowledgeObjects",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/knowledge/*"
    },
    {
      "Sid": "ManageResumeObjects",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/resumes/*"
    }
  ]
}
```

If the job-description attachment feature is added later, add its narrowly-scoped `job-descriptions/*` object ARN and API flow then. Avoid granting `s3:*` on all buckets.

When ready to cut over, set the four Lambda environment variables above and deploy the new container image built from the replacement branch. Keep `STORAGE_PROVIDER=supabase` until the bucket, policy, image build and tests are complete. The mode switch is not a bulk migration of existing Supabase files; old file objects remain in Supabase unless a separate copy/migration job is implemented.

## 7. CI / verification status

Isolated GitHub Actions workflow:
- File: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/blob/aws-service-replacements/.github/workflows/test-service-replacements.yml
- Latest known run: https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/runs/39587879520
- At snapshot, latest reported branch test workflow conclusion was **success**.
- Workflow runs Python compile checks over backend app/test files and unit tests for the S3 object provider and manager/employee/guest guard functions.
- These are isolated unit/syntax checks only. They do not prove live AWS S3 bucket permissions work, every API route is correctly scoped, or end-to-end uploads/recruitment workflows work after deployment.
- The normal backend image workflow in the main branch builds/pushes to ECR. The Lambda function still needs explicit update-function-code deployment unless an auto-update step is added and validated.
- The branch's normal image workflow and the additional isolated verification workflow should be reviewed together before merging. Don't accidentally deploy the new image to production while `STORAGE_PROVIDER=s3` points to a bucket that doesn't exist.

## 8. Required next steps for a new chat

Proceed in this order, showing current status and keeping production safe.

### Step A — Review the current branch carefully
1. Inspect the current `aws-service-replacements` head; do not assume it is still the SHA written here.
2. Review the role changes and S3 service changes as a diff against `main`.
3. Fix any security/logic issues found; run the existing GitHub Actions tests.
4. Add integration tests for manager/employee permissions (signup, job CRUD, candidate list/detail, evaluations, applications, document upload/delete/download, resume upload/screening, employee onboarding tasks/chat). Specifically check that a caller cannot change their own role or read another employee's private onboarding data.
5. Verify the public guest/demo behavior after restricting its privileges; don't silently break the live demo experience.

### Step B — S3 setup and staged upload cutover
1. Create a new private S3 bucket in Mumbai with Block Public Access and default encryption.
2. Add the exact prefix-limited policy to the Lambda execution role.
3. Update the branch/image pipeline to build from `aws-service-replacements` and deploy to Lambda only after checks pass. Do not assume updating ECR's `latest` tag updates Lambda automatically.
4. Initially smoke test upload/list/delete/download with a test PDF. Ensure the chatbot still processes/indexes the document in Qdrant and the binary file is persisted in S3.
5. Test resume upload and candidate detail/screening; verify signed download links expire and the UI can use them.
6. Only then set `STORAGE_PROVIDER=s3` in Lambda. Keep old Supabase objects intact for rollback.
7. Test existing old Supabase document/resume records and new S3 records separately. Document any need to backfill S3 metadata for previously uploaded knowledge documents.

### Step C — Cognito replacement (not started)
1. Decide the user migration strategy before changing authentication.
2. Configure an Amazon Cognito User Pool and app client in Mumbai; configure password/sign-in, email verification and token settings.
3. Use either a carefully tested migration trigger for first sign-in or bulk user import (bulk import may require password reset). AWS docs: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-import-users.html
4. Change frontend Supabase auth calls to Cognito login/signup/session handling, and change FastAPI JWT verification to Cognito issuer/JWKS/audience checks.
5. Map Cognito subject to existing profile rows without allowing a user-supplied role to confer Management access.
6. Test token refresh/expiry, logout, disabled users, role mapping, Vercel deployment env settings and CORS before cutover.
7. Do not remove Supabase Auth until rollback and account migration have been verified.

### Step D — Confirm database replacement
Ask user whether the intended extra service is RDS for PostgreSQL. If yes, compare running Supabase vs RDS cost, region, network implications, backup plan, migrations and connectivity before creating resources. RDS is not a drop-in replacement for the Supabase PostgREST client. The app has many direct calls such as `client.table(...)`; those must be refactored or a compatible API strategy provided. Be aware of Lambda networking and outbound connectivity to Gemini/Qdrant; don't add a NAT Gateway without cost approval.

### Step E — CloudWatch finalization
1. Confirm the Lambda execution role includes `AWSLambdaBasicExecutionRole`.
2. Set a reasonable explicit log-group retention period rather than leaving logs indefinitely.
3. Add low-noise alarms for Lambda Errors, throttles and duration/timeouts. Consider a cost/budget alert too.
4. Exercise health, login, job listing, job create/publish as manager, employee application flow, onboarding, chatbot, knowledge upload and resume screening; inspect logs on failures.
5. Make sure logs do not emit bearer tokens, JWTs, passwords, API keys or resume contents.

### Step F — Production release and cost safety
1. Keep replacement changes on the branch until CI and end-to-end smoke tests pass.
2. Create a reviewed PR into `main`; avoid blind merges.
3. Add an explicit workflow deployment step to call Lambda update for the newly pushed ECR image. Publish a Lambda version or use a stable alias if appropriate; verify rollback procedure.
4. Confirm production configuration and health after deployment.
5. Check AWS Billing and set a budget alarm. Be careful with RDS, NAT Gateway, EC2, ECR storage, Lambda usage and CloudWatch Logs; current billing dashboard may lag.

## 9. AWS official reference links

- Lambda execution roles and least privilege: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
- IAM best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- S3 Block Public Access: https://docs.aws.amazon.com/AmazonS3/latest/userguide/configuring-block-public-access-bucket.html
- S3 pre-signed URLs (private object sharing): https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html
- Cognito existing-user migration: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-import-using-lambda.html
- Lambda Function URLs/CORS: https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html
- Deploy/update Lambda container images: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

## 10. Starting prompt for the new chat

Use this prompt together with the README:

"Read the attached README fully and continue the AWS deployment/service replacements for `divyanshsaxena2209/enterprise-workplace-assistant`. First inspect the current `aws-service-replacements` branch and GitHub Actions run status, then review the diff for role-security mistakes and the S3 provider implementation. Keep `main` and the working Vercel + Lambda production app untouched until end-to-end checks pass. I need manager/employee authorization, S3 storage for chatbot knowledge documents and resumes (tell me separately if job-description attachments need a feature), Cognito migration, CloudWatch log retention/alarms, and confirmation whether RDS is the intended database replacement. Give manual AWS Console links and numbered steps, keep costs low, and do not ask me to paste secrets."
