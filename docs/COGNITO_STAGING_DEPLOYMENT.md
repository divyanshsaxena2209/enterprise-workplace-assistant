# Staging backend deployment (Cognito only)

## Why this is separate

The staging ECR image is built, the staging Supabase migrations are applied, and the pre-token-generation trigger is attached to the staging Cognito pool. A separate backend API is still required so the Vercel branch preview can call `COGNITO_ENABLED=true` without touching the Production Lambda.

This CloudFormation template is **opt-in**. It creates no resources until you deploy it. It creates one staging Lambda, a log group/role, and a public HTTPS Function URL. Requests other than the intentionally public health/auth bootstrap routes must pass the backend's authentication/authorization logic. The Function URL is public on the internet, so only use this stack for staging.

## Cost gate

Lambda invocations, compute, ECR storage, CloudWatch logs, and data transfer are usage-based. The CloudFormation stack is **not guaranteed to cost $0**. Before creating it, check AWS Billing / Free Tier and do not deploy if your available free allowance is unclear or if even a small charge is unacceptable.

## Deploy

1. Open [CloudFormation in Mumbai](https://ap-south-1.console.aws.amazon.com/cloudformation/home?region=ap-south-1).
2. Select **Create stack → With new resources (standard)**.
3. Upload `infra/aws/cognito-staging-backend.yml`.
4. Use stack name `ewa-cognito-staging-api`.
5. Keep the default image URI unless ECR no longer has this tag:
   `745531385877.dkr.ecr.ap-south-1.amazonaws.com/enterprise-workplace-assistant-backend:cognito-staging-0174c50b992222d01a87bea0f323e9196ddd511d`
6. For `SupabaseServiceRoleKey`, paste the **service-role secret for the isolated `workplace-assistant-staging` Supabase project only**. Retrieve it in that project's API keys settings. The parameter uses CloudFormation `NoEcho`; never paste the value in GitHub, a chat, or a screenshot. Never use the Production service-role key.
7. `SupabaseJwtSecret` is optional for this Cognito-only smoke test; leaving it blank means legacy Supabase HS256 bearer tokens will fail closed on this staging backend. Set it only to the staging project's JWT secret if you intend to exercise legacy Supabase JWTs as well.
8. Review the proposed resources and charges. Do not confirm the stack if the cost gate is not acceptable.
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
