# Staging backend deployment (Cognito only)

## Why this is separate

An earlier staging ECR image exists, the staging Supabase migrations are applied, and the pre-token-generation trigger is attached to the staging Cognito pool. That image predates the latest Management-access bootstrap changes. Before deploying those changes, build a fresh immutable staging image using the manual ECR workflow below. The API must remain separate from Production.

This CloudFormation template is **opt-in**. It creates no resources until you deploy it. It creates one staging Lambda, a log group/role, and a public HTTPS Function URL. Requests other than the intentionally public health/auth bootstrap routes must pass the backend's authentication/authorization logic. The Function URL is public on the internet, so only use this stack for staging.

## Cost gate

Lambda invocations, compute, ECR storage, CloudWatch logs, and data transfer are usage-based. The CloudFormation stack is **not guaranteed to cost $0**. Before creating it, check AWS Billing / Free Tier and do not deploy if your available free allowance is unclear or if even a small charge is unacceptable. The proposed staging Lambda is limited to **two concurrent executions** to reduce parallel compute spend. This is not a hard cap on total requests or a substitute for authenticated route checks; the public Function URL must remain staging-only.

## Deploy

1. Open [CloudFormation in Mumbai](https://ap-south-1.console.aws.amazon.com/cloudformation/home?region=ap-south-1) and inspect whether `ewa-cognito-staging-api` already exists. **Update it if present; do not create a duplicate Lambda stack/function.** Create a new stack only if you have confirmed no staging stack exists.
2. Open [the manual ECR build workflow](https://github.com/divyanshsaxena2209/enterprise-workplace-assistant/actions/workflows/build-cognito-staging-ecr.yml), choose **Run workflow**, and select branch `cognito-staging-integration`. Do this only after its source CI passes and the cost gate is acceptable. The successful run builds an immutable tag `cognito-staging-<commit-sha>`.
3. In CloudFormation, select **Update** for the existing stack (or **Create stack → With new resources (standard)** only if no stack exists), upload `infra/aws/cognito-staging-backend.yml`, and use stack name `ewa-cognito-staging-api`. Enter `ImageUri` using the exact immutable ECR tag produced by the successful workflow. The template no longer supplies an old image as a default.
4. Set `ManagementEmailAllowlist` to the comma-separated verified email address(es) trusted to receive initial Management application access immediately. For the first manager, use the actual verified Cognito email intended to administer this workspace. Leave it blank if all Management access must wait for approval by an existing Management account. This is **application access**, not AWS IAM credentials for the user.
5. For `SupabaseServiceRoleKey`, keep the existing parameter value when updating the stack, or enter the **service-role secret for the isolated `workplace-assistant-staging` Supabase project only** if CloudFormation requires it. The parameter uses `NoEcho`; never paste the value in GitHub, a chat, or a screenshot. Never use the Production service-role key.
6. `SupabaseJwtSecret` is optional for this Cognito-only smoke test; leaving it blank means legacy Supabase HS256 bearer tokens will fail closed on this staging backend. Keep it blank unless you intentionally need to test legacy staging Supabase JWTs.
7. Keep `StorageProvider=supabase` for this first Cognito/role smoke test. Review the proposed resources and charges before confirming; do not deploy if the cost gate is not acceptable.

The `StorageProvider` parameter defaults to `supabase`; keep that default for the first Cognito/role smoke test. Optional S3 cutover is documented in [S3_STAGING_SETUP.md](S3_STAGING_SETUP.md). Only choose `StorageProvider=s3` after the private staging bucket exists and you can provide its exact name through `DocumentBucketName`. CloudFormation adds only object-level permissions for the `knowledge/*` and `resumes/*` prefixes; it does not create the bucket in this stack.

9. After CREATE_COMPLETE, copy the stack outputs:
   - `StagingApiFunctionUrl` — staging API base URL.
   - `CognitoLinkApiUrl` — account-link endpoint.
   - `PreviewCallbackUrl` and `PreviewSignOutUrl` — values to register on the staging Cognito app client.

## Post-deploy verification

1. Open the `StagingApiFunctionUrl` output with `health` appended. Expect JSON with `status: ok` and `environment: staging`.
2. Do not point the current Production frontend at this URL. Cognito environment variables must be set only for Vercel Preview branch `cognito-staging-integration`.
3. Configure the app client’s allowed callback/default redirect to the stack’s `PreviewCallbackUrl` (the Vercel preview origin plus `/auth/callback`) and sign-out URL to `PreviewSignOutUrl` (same origin plus `/login`). Remove the old CloudFront-root callback only after the `/auth/callback` entry is saved and confirmed. That root URL displayed Cognito’s generic success page and did not process the authorization code.
4. Vercel Preview variables must point to the staging Supabase URL, its browser-safe publishable/anon key, this staging API URL, Cognito domain/client ID, callback/sign-out URLs, link endpoint and the app client's configured refresh-token lifetime. Keep the shared Production variables unchanged.
5. Run one consolidated end-to-end test from the staging branch `/signup`: authenticate through Cognito, process `/auth/callback`, provision an employee profile in staging, link the Cognito subject, call a protected API as employee, verify a manager-only action is denied to that employee, verify direct authenticated interview access is denied by Supabase RLS, then test refresh/logout. Never use Production credentials or data as test fixtures.

## Not included

- No changes to Production Lambda, Vercel Production environment, Production Supabase, or Cognito Production pool.
- No S3 bucket; `STORAGE_PROVIDER` stays `supabase`.
- Gemini/Qdrant keys are not copied into staging by this template. Features requiring them remain unavailable until separately configured.
