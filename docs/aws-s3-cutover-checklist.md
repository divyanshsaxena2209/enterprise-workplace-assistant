# S3 Cutover Checklist (Manual AWS Setup)

This document applies only to the `aws-service-replacements` branch. It does not change production until merged, built, deployed, and `STORAGE_PROVIDER=s3` is set in the Lambda environment.

## 1. Create a private bucket

Open [Amazon S3 buckets in ap-south-1](https://s3.console.aws.amazon.com/s3/buckets?region=ap-south-1) and create a unique bucket name such as `ewa-private-documents-<unique-suffix>`.

Recommended settings:
- AWS Region: `ap-south-1` (Mumbai).
- Object Ownership: Bucket owner enforced.
- Block all public access: enabled (all four options).
- Default encryption: SSE-S3 (S3-managed keys).
- Do not add a public bucket policy or public ACL.
- Keep versioning disabled initially to minimize storage accumulation; decide later if rollback/version history is needed.

## 2. Add a least-privilege policy to the existing Lambda execution role

Open [IAM Roles](https://console.aws.amazon.com/iam/home#/roles), open the execution role shown under Lambda → Configuration → Permissions, then add an inline policy replacing `YOUR_BUCKET_NAME` with the bucket's exact name:

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

Do not attach this policy to the GitHub Actions OIDC role; these object permissions belong on the Lambda execution role. Do not put AWS access keys in Lambda environment variables.

## 3. Deploy only after reviewing the branch

Required Lambda environment variables:
- `STORAGE_PROVIDER=s3`
- `AWS_REGION=ap-south-1`
- `AWS_S3_BUCKET=<exact bucket name>`
- `S3_PRESIGNED_URL_TTL_SECONDS=900`

Keep `STORAGE_PROVIDER=supabase` until the S3 bucket, IAM policy, image build, and tests are complete. Setting it to `s3` changes new knowledge-document and resume uploads to S3; it does not automatically migrate old files. Existing Supabase URLs/objects remain where they are until a separate migration is planned.

## What S3 stores in this app

- Chatbot / Knowledge Base: the original PDF/DOCX file under `knowledge/`. Text chunks/embeddings remain in Qdrant so retrieval can work.
- Resume uploads: the original PDF/DOCX file under `resumes/`. Parsed candidate data and the resume record remain in the relational database.
- Job listings: the current form writes title, description, requirements, department, status, etc. as database fields; it does not upload a file. Do not copy listing text to S3. If a Job Description attachment feature is added later, give it a separate `job-descriptions/` prefix and store its object key in the database.

## 4. Smoke-test after deployment

1. Health endpoint returns `status: ok`.
2. Upload a small test PDF from the Knowledge Base; verify the returned provider is `s3` and a key starts with `knowledge/`.
3. Open the document; the backend should issue a fresh, expiring presigned URL.
4. Delete the test document and confirm it is removed from storage and Qdrant.
5. Upload a test resume, open the candidate detail page, and verify the resume can load through a short-lived presigned URL.
6. Confirm normal job/candidate application flow still works.

Only after those tests pass should the production provider be switched. Keep existing Supabase Storage objects for rollback until a separate migration confirms all required files have been copied.