# Staging Demo Verification Checkpoint — 26 October 2026

Repository: `divyanshsaxena2209/enterprise-workplace-assistant`  
Branch: `cognito-staging-integration`  
Environment: isolated staging only  
Status: **Knowledge Base chatbot functional verification DONE for the tested behaviors; overall demo verification remains PARTIAL because provider reliability and other application workflows are not fully verified.**

## User-observed Knowledge Base chatbot results

The user manually tested the chatbot in the staging Vercel branch preview with the fictional `Northstar Meridian Employee Policy Handbook Test Document` uploaded and indexed. The chatbot cited the document as its source (PDF pages 1–9).

| Test | Observed result | Status |
|---|---|---|
| Annual leave: “How many annual leave days does a full-time employee receive per year?” | Returned 18 working days per completed leave year, accruing at 1.5 days per month, with a caveat for applicable law/individual terms. | **PASS** — consistent with the tested handbook |
| Parental leave: “What parental leave benefits are available to employees, and what eligibility conditions must they meet?” | Said the document did not specify parental leave; then listed annual, sick and casual leave information from the handbook. | **PASS** — appropriate abstention rather than inventing a parental entitlement |
| Overtime: “If an employee works extra hours over the weekend to finish a project, are they automatically entitled to overtime pay?” | Said no automatic entitlement; described prior manager approval, an emergency exception, and legal requirements. | **PASS** — consistent with the answer observed from the handbook |
| Confidentiality incident: “I accidentally sent a confidential company document to my personal email address. What should I do?” | Returned a Gemini high-demand message. CloudWatch later showed HTTP 503 responses for several models, followed by HTTP 404 responses for legacy/unavailable model IDs; all fallback models were exhausted. | **Provider availability failure identified** — not a successful policy-answering test; model fallback configuration fix committed for staging, but deployment/runtime verification remains pending |

The three successful answers demonstrated that the chatbot can retrieve the uploaded handbook, cite its PDF pages, answer policy questions, and abstain when the handbook does not specify an answer. **Mark the Knowledge Base chatbot's functional/document-retrieval verification DONE for these tested behaviors.** This is a bounded verification result, not a claim that every chatbot edge case or service-availability condition is verified. One response failed because Gemini returned provider errors, so operational resilience is tracked separately below.

## Gemini key and service-error follow-up

- On 26 October, the user confirmed the newly created Gemini API key was pasted into the existing staging Lambda before the latest logs were captured. The key value is intentionally not recorded.
- CloudWatch now confirms the failing request reached Gemini and received HTTP 503 `UNAVAILABLE` / high-demand responses from multiple model IDs. The logs also show HTTP 404 errors for `gemini-1.5-flash` and `gemini-2.5-flash` in this project/API context. These errors are not evidence of a bad API key.
- Code change committed on `cognito-staging-integration`: `f7bbbe5c7258879213bdf6fc53442715cc1db01c` updates `backend/app/services/llm_fallback.py` to prefer documented model IDs (`gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) and remove the known 404 fallback IDs. Google’s current model list documents these IDs. This commit has **not yet been confirmed built/deployed to Lambda**, and its fallback models have not yet been live-smoke-tested.
- Operational resilience remains open: once CI/build/deployment is complete, make one chatbot request and confirm a successful answer or a clear bounded provider error. Do not keep creating API keys for HTTP 503 service-capacity errors.
- Earlier CloudWatch evidence included a Lambda invocation that timed out after 60 seconds during `get_session_messages` for session `b806d9c9-7393-47e6-a5f8-0e1fd81e6f3a`. That is a separate backend/session-retrieval concern to investigate if it recurs; do not assume the Gemini key fixes it.
- Keep secrets, API keys, access tokens and authorization codes out of this file and all screenshots/messages.

## Overall demo verification matrix

| Area | Current evidence | Status |
|---|---|---|
| Staging Cognito authentication / profile mapping / Employee–Management access | Previously user-confirmed staging flow; see main handoff for checkpoint and limitations. | **User-confirmed pass for reported flow**, not a substitute for every route-level authorization test |
| Staging Lambda health | User loaded the staging `/health` endpoint and observed `status=ok`, `environment=staging`; CloudWatch showed a successful short invocation with no traceback in that health request. | **PASS for health endpoint only** |
| CloudWatch logs | User shared successful invocation START/END/REPORT entries; another request later timed out after 60 seconds. | **PARTIAL** — logs are delivered, but timeout diagnosis remains open if reproducible |
| Knowledge Base document upload and indexing | A handbook PDF was indexed and appeared in cited records for three generated answers. | **PARTIAL PASS** — these observations demonstrate retrieval; storage-provider migration and delete/download lifecycle still need their own tests |
| Knowledge Base question answering | Three observed answers were grounded in the cited handbook; one question hit Gemini HTTP 503 errors and stale fallback model IDs (404). | **FUNCTIONAL VERIFICATION DONE for tested behaviors; provider resilience fix pending deployment and smoke test** |
| Gemini replacement key | User confirmed the new key was copied into the staging Lambda before the latest logs. Requests reach Gemini but provider/model errors persist. | **CONFIGURATION UPDATED; functional success after key change not demonstrated** |
| Qdrant staging connection | User reported adding `QDRANT_URL` and `QDRANT_API_KEY` to staging configuration. The successful indexed/cited responses are positive functional evidence, but configuration values must never be recorded here. | **Functionally demonstrated for those successful queries** |
| Jobs & hiring, onboarding, resume processing/evaluation, management/employee restrictions across all routes | No complete end-to-end evidence recorded in this checkpoint. | **NOT FULLY VERIFIED** |
| S3 document storage | Staging provider was previously confirmed as `STORAGE_PROVIDER=supabase` with `AWS_S3_BUCKET` empty. | **NOT ACTIVE; separate optional migration** |
| Production isolation | Project process requires Production remain unchanged; this checkpoint documents staging observations only. | Continue to verify no Production changes before release |

## Decision: chatbot verification vs. overall demo verification

**Knowledge Base chatbot functional verification: DONE for the behaviors tested.** The evidence confirms successful document retrieval/citations, a correct direct policy answer, appropriate abstention for an absent policy, and a relevant overtime answer. Record the Gemini 503 failure separately as an operational reliability issue; it does not erase the successful functional checks.

**Overall application/demo verification: NOT COMPLETE.** Remaining work:
1. Run CI/build for commit `f7bbbe5c7258879213bdf6fc53442715cc1db01c`, then deploy the resulting staging image through the existing staging-only process. Do not change Production.
2. After deployment, make one low-volume chatbot request to verify the new model fallback chain. If Gemini still returns 503, capture the sanitized error and treat it as provider availability rather than creating more keys. Investigate the earlier `get_session_messages` 60-second timeout if it recurs.
3. Complete a targeted staging smoke test for Jobs & Hiring, onboarding, resume/evaluation workflow if used in the demo, and Employee-vs-Management authorization boundaries.
4. Confirm document upload/index, question answering, download and deletion/cleanup behavior for the currently active Supabase storage provider. S3 is not active and is not required for the current demo unless explicitly chosen.
5. Keep Production untouched and do not merge draft migration PRs merely because these chatbot checks pass.

## Official Gemini error handling reference

- [Gemini API troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting) — Google recommends bounded exponential backoff for retryable 429/5xx errors and distinguishes service-capacity errors from invalid-key/project configuration errors.
- [Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors) — reference for authentication, quota, rate-limit, and service-unavailable codes.

## Resume application failure — root cause confirmed and fix prepared (26 October 2026)

### User-visible errors
The employee Apply for Position modal showed two failures during resume submission:
- `Failed to structure the resume data.`
- `Failed to save candidate and resume records after upload; object cleanup was attempted.`

### Evidence and root cause
- The first error occurred before storage/database persistence, while the resume parser called Gemini. CloudWatch showed several model availability failures (503) and legacy/unavailable model IDs (404); the model fallback chain is corrected in this staging change.
- Supabase staging edge logs at `2026-10-25T19:33:27Z` show the resume PDF upload to the private `resumes` bucket succeeded (HTTP 200), the candidate insert succeeded (HTTP 201), the resume insert failed with HTTP 400 / PostgREST `PGRST204`, and storage cleanup returned HTTP 200.
- The live staging `public.resumes` schema uses `id, candidate_id, file_name, file_url, parsed_json, uploaded_at`. The backend was incorrectly sending `parsed_data` (not a live column) and omitting required `file_name`. This explains the second failure.
- The failed attempt left one candidate row created at `2026-10-25T19:33:27.947654Z` with no resume and no application. That staging test orphan is scheduled for narrowly scoped cleanup after a final recheck.
- No Production resources or data were modified.

### Code changes prepared for staging
- Send `file_name` and `parsed_json` from the resume-upload route.
- Build an explicit DB insert payload in `CandidateRepository` using actual schema columns, and roll back the just-created candidate if resume insert fails.
- Make the API response schema read both current `parsed_json/uploaded_at` fields and legacy `parsed_data/created_at` fields, with a stable `UPLOADED` API status default.
- Replace unsupported/stale fallback IDs with currently documented stable Gemini model IDs, preferring Flash-Lite first to reduce cost. Official model list: https://ai.google.dev/gemini-api/docs/models. Google recommends bounded fallback/backoff for 429/5xx and checking model/API compatibility: https://ai.google.dev/gemini-api/docs/troubleshooting.
- Add regression tests for the live database payload, candidate rollback, and schema compatibility.

### Release status
These changes must pass the staging branch GitHub Actions test workflow and ECR image build. The new image must then be deployed to the existing `ewa-cognito-staging-api` CloudFormation stack through a reviewed, modify-in-place change set. Production stays untouched. After deployment, verify one real PDF upload succeeds, creates the application, and can be reopened/downloaded from the candidate details route. Do not repeat uploads before the new image is live.

