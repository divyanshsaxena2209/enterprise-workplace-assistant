# Staging Demo Verification Checkpoint — 26 October 2026

Repository: `divyanshsaxena2209/enterprise-workplace-assistant`  
Branch: `cognito-staging-integration`  
Environment: isolated staging only  
Status: **PARTIAL PASS — the Knowledge Base chatbot's document retrieval and policy answering are demonstrated, but the whole application is not fully verified.**

## User-observed Knowledge Base chatbot results

The user manually tested the chatbot in the staging Vercel branch preview with the fictional `Northstar Meridian Employee Policy Handbook Test Document` uploaded and indexed. The chatbot cited the document as its source (PDF pages 1–9).

| Test | Observed result | Status |
|---|---|---|
| Annual leave: “How many annual leave days does a full-time employee receive per year?” | Returned 18 working days per completed leave year, accruing at 1.5 days per month, with a caveat for applicable law/individual terms. | **PASS** — consistent with the tested handbook |
| Parental leave: “What parental leave benefits are available to employees, and what eligibility conditions must they meet?” | Said the document did not specify parental leave; then listed annual, sick and casual leave information from the handbook. | **PASS** — appropriate abstention rather than inventing a parental entitlement |
| Overtime: “If an employee works extra hours over the weekend to finish a project, are they automatically entitled to overtime pay?” | Said no automatic entitlement; described prior manager approval, an emergency exception, and legal requirements. | **PASS** — consistent with the answer observed from the handbook |
| Confidentiality incident: “I accidentally sent a confidential company document to my personal email address. What should I do?” | Returned: “The AI model is currently experiencing exceptionally high demand. This is a temporary spike. Please wait a moment and try your query again.” | **FAILED ATTEMPT / RETEST REQUIRED** — no policy answer was generated; this does not by itself establish a retrieval failure |

The three successful answers showed that the chatbot could retrieve the uploaded handbook and answer both direct policy questions and a question whose answer was absent from the document. The fourth attempt was not a policy-answering pass. Retry it once and compare any answer to the actual handbook text.

## Gemini key and service-error follow-up

- On 26 October, the user created a new Gemini API key in Google AI Studio. At the time of this report, the user explicitly said the new key had **not yet been copied into the staging Lambda environment**.
- Do not mark the new key as deployed or tested until the user updates `GEMINI_API_KEY` on the existing staging Lambda and a fresh request succeeds.
- The displayed “exceptionally high demand” message is consistent with a transient Gemini service-capacity error, but the UI message alone does not establish the exact HTTP status or root cause. Inspect the corresponding CloudWatch invocation for a sanitized provider status/error. Follow Google’s transient-error guidance (bounded retry with exponential backoff for 429/5xx); do not keep creating keys for a service-capacity error.
- Earlier CloudWatch evidence included a Lambda invocation that timed out after 60 seconds during `get_session_messages` for session `b806d9c9-7393-47e6-a5f8-0e1fd81e6f3a`. That is a separate backend/session-retrieval concern to investigate if it recurs; do not assume the Gemini key fixes it.
- Keep secrets, API keys, access tokens and authorization codes out of this file and all screenshots/messages.

## Overall demo verification matrix

| Area | Current evidence | Status |
|---|---|---|
| Staging Cognito authentication / profile mapping / Employee–Management access | Previously user-confirmed staging flow; see main handoff for checkpoint and limitations. | **User-confirmed pass for reported flow**, not a substitute for every route-level authorization test |
| Staging Lambda health | User loaded the staging `/health` endpoint and observed `status=ok`, `environment=staging`; CloudWatch showed a successful short invocation with no traceback in that health request. | **PASS for health endpoint only** |
| CloudWatch logs | User shared successful invocation START/END/REPORT entries; another request later timed out after 60 seconds. | **PARTIAL** — logs are delivered, but timeout diagnosis remains open if reproducible |
| Knowledge Base document upload and indexing | A handbook PDF was indexed and appeared in cited records for three generated answers. | **PARTIAL PASS** — these observations demonstrate retrieval; storage-provider migration and delete/download lifecycle still need their own tests |
| Knowledge Base question answering | Three observed answers were grounded in the cited handbook; one question hit a provider-style high-demand message. | **PARTIAL PASS** |
| Gemini replacement key | Key created in AI Studio, but not yet copied to Lambda at the time recorded. | **PENDING** |
| Qdrant staging connection | User reported adding `QDRANT_URL` and `QDRANT_API_KEY` to staging configuration. The successful indexed/cited responses are positive functional evidence, but configuration values must never be recorded here. | **Functionally demonstrated for those successful queries** |
| Jobs & hiring, onboarding, resume processing/evaluation, management/employee restrictions across all routes | No complete end-to-end evidence recorded in this checkpoint. | **NOT FULLY VERIFIED** |
| S3 document storage | Staging provider was previously confirmed as `STORAGE_PROVIDER=supabase` with `AWS_S3_BUCKET` empty. | **NOT ACTIVE; separate optional migration** |
| Production isolation | Project process requires Production remain unchanged; this checkpoint documents staging observations only. | Continue to verify no Production changes before release |

## Decision: is the application completely verified?

**No.** Mark only the observed chatbot cases and staging health/authentication evidence above at their stated level. A few successful chatbot responses do not establish complete application verification. Outstanding acceptance work includes:
1. Update the newly created Gemini key in the existing staging Lambda, then retry the failed confidentiality question once.
2. If the chatbot hangs or returns another provider error, correlate that attempt with sanitized CloudWatch logs and diagnose any repeated session-message timeout.
3. Complete a small, targeted staging smoke test for Jobs & Hiring, onboarding, resume/evaluation workflow if used in the demo, and Employee-vs-Management authorization boundaries.
4. Confirm document upload/index, question answering, download and deletion/cleanup behavior appropriate to the currently active Supabase storage provider. S3 is not required for the current demo unless explicitly chosen as a separate scope.
5. Keep Production untouched and do not merge draft migration PRs merely because this partial demo checkpoint passes.

## Official Gemini error handling reference

- [Gemini API troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting) — Google recommends bounded exponential backoff for retryable 429/5xx errors and distinguishes service-capacity errors from invalid-key/project configuration errors.
- [Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors) — reference for authentication, quota, rate-limit, and service-unavailable codes.

