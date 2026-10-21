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

## Least-privilege staging Lambda policy

After the staging bucket exists, create a **new inline policy** and attach it only to the staging Lambda execution role. Replace `REPLACE_WITH_STAGING_BUCKET_NAME` with the exact bucket name output above:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AccessOnlyStagingDocumentObjects",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::REPLACE_WITH_STAGING_BUCKET_NAME/knowledge/*",
        "arn:aws:s3:::REPLACE_WITH_STAGING_BUCKET_NAME/resumes/*"
      ]
    }
  ]
}
```

The policy deliberately grants no bucket listing, bucket administration, public access, or access to other prefixes.

## Staging environment variables

Set these only on a separate staging backend after the bucket and IAM role are verified:

- `STORAGE_PROVIDER=s3`
- `AWS_REGION=ap-south-1`
- `AWS_S3_BUCKET=<the staging bucket name>`
- `S3_PRESIGNED_URL_TTL_SECONDS=900`

Do not add AWS access keys. The AWS SDK must obtain credentials from the staging Lambda execution role.

## Before switching the staging provider

1. Confirm the bucket is private and the staging role can put/get/delete only objects under `knowledge/` and `resumes/`.
2. Run `backend/tests/test_object_storage.py` and the full service-replacement CI.
3. Test knowledge-document upload, RAG ingestion, resume upload/download, and deletion using non-sensitive test files.
4. Verify that persisted records use `storage_provider=s3` and preserve the object key; presigned URLs expire and must not be treated as permanent file URLs.
5. Keep Production on Supabase Storage until all tests pass and there is an explicitly approved migration/rollback plan. Existing Supabase objects are not copied by this change.
