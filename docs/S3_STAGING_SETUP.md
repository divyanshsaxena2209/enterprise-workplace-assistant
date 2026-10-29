# Private S3 storage — staging only

## Current state

- The backend storage adapter supports `STORAGE_PROVIDER=s3` for `knowledge/` and `resumes/` objects.
- The default remains `STORAGE_PROVIDER=supabase`; do not change it for Production.
- `infra/aws/private-document-storage.yml` is an opt-in CloudFormation template. It creates nothing unless a human deploys it.
- This repository change does not create an S3 bucket, change an IAM role, or deploy a Lambda.

## Cost and safety gate

S3 has usage-based charges for stored bytes, requests, and data transfer. The bucket itself has no fixed setup fee, but it is **not guaranteed to cost $0**. Check the AWS Billing/Free Tier view before deploying. Do not deploy this stack if your available free allowance or credits are unclear.

Use a dedicated staging bucket and a separate staging Lambda execution role. Do not attach these permissions to the Production Lambda role and do not change the Production `AWS_S3_BUCKET` or `STORAGE_PROVIDER` settings.

## Deploy only when explicitly ready

1. Open [CloudFormation in ap-south-1](https://ap-south-1.console.aws.amazon.com/cloudformation/home?region=ap-south-1).
2. Choose **Create stack → With new resources (standard)**.
3. Upload `infra/aws/private-document-storage.yml` from this branch.
4. Enter a globally unique bucket name. Review the template and cost implications before creating the stack.
5. Record the output bucket name. Keep Block Public Access enabled; do not add public-read ACLs or policies.

## Connect the bucket to the staging Lambda

The staging Cognito backend template now supports optional S3 storage with a least-privilege role policy. It defaults to Supabase Storage and creates **no bucket** itself.

After the private bucket is created:

1. If `ewa-cognito-staging-api` already exists, open that CloudFormation stack and choose **Update**. If it does not exist yet, create it using `infra/aws/cognito-staging-backend.yml` and apply the parameters below during initial creation.
2. Keep the current immutable `ImageUri` unless a newer CI-verified image is documented.
3. Set `StorageProvider=s3` and `DocumentBucketName` to the exact staging bucket name.
4. Leave Production variables and the Production Lambda untouched. Do not create or paste AWS access keys; the SDK uses the separate staging Lambda execution role.

The stack update automatically attaches a policy granting only `s3:PutObject`, `s3:GetObject`, and `s3:DeleteObject` for that bucket's `knowledge/*` and `resumes/*` prefixes. It does not grant bucket listing, bucket administration, public access, or access to other prefixes. CloudFormation rejects `StorageProvider=s3` if the bucket name is blank.

## Staging environment variables

The template sets these values for the staging Lambda when the stack is updated:

- `STORAGE_PROVIDER=s3`
- `AWS_S3_BUCKET=<the staging bucket name>`
- `S3_PRESIGNED_URL_TTL_SECONDS=900`

The Lambda runtime supplies `AWS_REGION` automatically. Do not try to override that reserved runtime variable, and do not add AWS access keys. The AWS SDK must obtain credentials from the staging Lambda execution role.

## Before switching the staging provider

1. Confirm the bucket is private and the staging role can put/get/delete only objects under `knowledge/` and `resumes/`.
2. Run `backend/tests/test_object_storage.py` and the full service-replacement CI.
3. Test knowledge-document upload, RAG ingestion, resume upload/download, and deletion using non-sensitive test files.
4. Verify that persisted records use `storage_provider=s3` and preserve the object key; presigned URLs expire and must not be treated as permanent file URLs.
5. Keep Production on Supabase Storage until all tests pass and there is an explicitly approved migration/rollback plan. Existing Supabase objects are not copied by this change.

## Migrate existing referenced files after S3 cutover

Once the S3-enabled backend image is deployed, use the staging-only migration endpoint rather than manually uploading files in the S3 console. The endpoint is restricted to Management, refuses any environment other than `staging`, and requires `STORAGE_PROVIDER=s3` plus a configured bucket.

Endpoint: `POST /api/v1/knowledge/storage/migrate-existing-to-s3`

1. Open the staging backend's `/docs` page and authorize with the existing staging Management access token (never paste it into chat or GitHub).
2. First send JSON body `{"dry_run": true}`. Expected plan is one registered knowledge document and three resume records, because the current staging database and Supabase `resumes` bucket inventory each show those four referenced objects.
3. Review the returned counts and ensure no unsupported/missing references are reported.
4. If the dry run is clean, send `{"dry_run": false}` once. The backend downloads each source object from Supabase, uploads it to S3 under `knowledge/<source-key>` or `resumes/<source-key>`, reads the destination back and compares SHA-256, and only then updates the corresponding database reference. Repeats are idempotent for already migrated rows.
5. Source Supabase objects are deliberately retained. Do not delete them as part of this migration. If a copy or reference update fails, inspect the sanitized result and CloudWatch logs before retrying.
6. Verify the Knowledge Base document still appears and answers a semantic question using the existing Qdrant chunks; verify authorized download and deletion behavior with a non-sensitive document. Also verify existing candidate resume downloads and, if applicable, re-screen one synthetic resume.

This copies referenced files only; it does not bulk-import unrelated objects. Qdrant embeddings/chunks are not re-created or modified by the migration because this operation only changes original-file storage. Rollback remains possible while the original Supabase objects are retained.

## Private Supabase fallback while S3 remains opt-in

The backend's storage provider still defaults to `supabase`, and the staging project's existing `resumes` bucket is private (`public=false`). New Supabase-backed knowledge and resume uploads now persist stable object keys instead of exposing `get_public_url()` links. The API generates short-lived signed URLs only after the request has passed the role and, for knowledge documents, department-scope checks. See the [Supabase Python signed-URL reference](https://supabase.com/docs/reference/python/storage-from-createsignedurl).

This fallback does not enable S3 or alter bucket visibility. S3 remains an opt-in cutover requiring a private staging bucket and the least-privilege Lambda execution-role policy. Existing resume rows with Supabase public-URL-shaped values are parsed into a safe object key and converted to a short-lived signed URL without fetching the supplied URL. Legacy documents absent from the trusted knowledge registry must be re-uploaded/registered before employees can retrieve them; unscoped Qdrant records are fail-closed for employees.
