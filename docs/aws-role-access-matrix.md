# Manager and Employee Access Matrix

These are application roles, not AWS account administrator roles. In the Cognito migration branch, the FastAPI backend validates Supabase or Cognito tokens and resolves the user's application role and active state from the existing Supabase profile record. Cognito identities map to profile IDs through the server-only identity mapping table. The live Cognito browser flow remains an end-to-end gate. The Lambda execution role is a workload identity and must not be assigned separately to ordinary employees.

| Capability | Management | Employee | Guest demo |
|---|---:|---:|---:|
| View published job listings | Yes | Yes | Yes (read-only) |
| View draft/archived job listings | Yes | No | No |
| Create, edit, publish, archive, delete job listings | Yes | No | No |
| View candidate list, candidate detail, resumes and recruitment scores | Yes | No | No |
| Upload a candidate's resume for screening | Yes | Yes | No |
| Submit an application | No | Yes (own identity) | No |
| View applications | All, for recruitment work | Own applications only | No |
| Approve/reject candidates, move pipeline, add recruiter notes | Yes | No | No |
| Create an employee onboarding record | Yes | No | No |
| Read onboarding tasks and ask onboarding assistant | Any employee | Own record only | No |
| Upload/delete company knowledge documents | Yes | No | No |
| Query chatbot and read allowed knowledge documents | Yes | Yes | Demo read-only access |
| Access private S3 using AWS credentials directly | No | No | No |

## Enforcement principles

- Apply server-side FastAPI dependencies and service/repository scope checks. Frontend hiding is only user experience; it is not security enforcement.
- Only a trusted administrator should provision or promote Management users. Public signup must not allow a caller to self-select Management.
- The public guest token is a demo identity, not an account. It must never satisfy management or employee write permissions.
- Lambda gets a least-privilege IAM policy for private `knowledge/*` and `resumes/*` S3 objects. The backend checks app roles before returning a presigned link or changing objects.
- Presigned URLs are bearer links: anyone who receives the URL can use it until expiry, so keep their lifetime short and return them only after authorization.
- Job listings are relational records (title, description, requirements, status) in the database. The current job schema has no attachment-upload field. Raw uploaded chatbot documents and resume files belong in S3; if job-description PDF attachments are added, store those file objects under a separate `job-descriptions/` prefix and keep the searchable job record in the database.

## Review / limitations

These rules are implemented/staged on `cognito-staging-integration` and are proposed for `aws-service-replacements` through draft PR #3 and PR #1. They are not production-cutover evidence. The S3 object provider defaults to `supabase` until a private bucket exists, the staging Lambda execution-role policy is applied, and resume plus knowledge-document smoke tests pass. Role-unit tests run in GitHub Actions, but application-role behavior still needs live staging E2E verification.
