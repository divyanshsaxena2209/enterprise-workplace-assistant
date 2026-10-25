# AWS staging frontend hosting — safe migration plan

Date: 26 October 2026  
Repository: `divyanshsaxena2209/enterprise-workplace-assistant`  
AWS hosting branch: `aws-frontend-hosting-staging`

## Decision from code inspection

The current frontend is a Next.js 15.5 App Router application and is **not a static-only site today**. It has:
- Next.js middleware that performs Cognito session-gate routing and Supabase session middleware.
- Dynamic route handlers at `/api/auth/cognito/start`, `/api/auth/cognito/access-token`, `/api/auth/cognito/logout`, and `/auth/callback`.
- Server-side cookie operations for OAuth state, nonce, PKCE verifier, refresh tokens, and logout.

These handlers depend on each incoming request and set/clear HttpOnly cookies. Next.js documents that static export does not support dynamic Route Handlers, request cookies, redirects/rewrites, headers, or middleware/proxy features. Therefore **do not add `output: "export"` or try to upload a plain `out/` folder to S3**: that would break sign-in/session refresh/logout and OAuth callbacks.

For the requested fast, low-risk move to AWS, this proof of concept uses **AWS Amplify Hosting Compute for Next.js 15**. Amplify manages the Next.js server runtime and uses managed S3/CloudFront delivery for assets. It is AWS-hosted with assets stored/served through S3/CloudFront, but it is not a self-managed raw S3 static website. If a customer-managed S3 bucket for all frontend files is mandatory, that would require a larger follow-on refactor to relocate the server-side auth routes and session logic.

Official guidance:
- Next.js static export limitations: https://nextjs.org/docs/app/guides/static-exports
- Amplify supports Next.js 15 SSR and middleware: https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html
- Amplify SSR monorepo build settings: https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html
- Amplify pricing: https://aws.amazon.com/amplify/pricing/

## Vercel preservation / rollback baseline

No Vercel project settings, environment variables, domains, or deployments were changed by this preparation.

Verified before the AWS work:
- Vercel project: `enterprise-workplace-assistant` (project ID `prj_ap3BHcwJymfIxo2ABdaBegLJRLBh`).
- Existing latest READY deployment: [open preview](https://enterprise-workplace-assistant-ps805if6u-divyansh-50b7.vercel.app).
- Deployment ID: `dpl_HcyeaVFZcjHVyRydRzgWA5Ut9XQU`.
- Source commit: `921f844c4f70609fe31a57ff89767dd9b9c2aa74` (`docs: mark staging demo verification complete`).
- Vercel project domains were left unchanged.

That immutable Vercel URL remains the rollback/reference deployment. This branch is separate, so the AWS hosting work does not replace the existing staging branch's Vercel deployment.

## Amplify build config

Root-level `amplify.yml`:
- Uses monorepo app root `frontend`.
- Runs `npm ci` and `npm run build` from the frontend root.
- Publishes Next.js `.next` build artifacts (SSR mode; not static export).
- Exposes only allow-listed frontend/runtime configuration to Next.js via `.env.production`.
- Does not pass backend-only secrets such as `GEMINI_API_KEY`, `QDRANT_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `SUPABASE_JWT_SECRET` to the frontend build/runtime.

When creating the app in Amplify, select the repository `divyanshsaxena2209/enterprise-workplace-assistant`, branch `aws-frontend-hosting-staging`, and indicate that it is a monorepo with application root `frontend`. Use the default Standard build instance and do not enable AWS WAF or other paid extras.

## Environment variables in Amplify

Set the following in the Amplify branch's environment-variable settings. Copy the existing **staging Preview** values from Vercel as applicable, but use the new Amplify branch URL for the callback/sign-out values:
- `AMPLIFY_MONOREPO_APP_ROOT=frontend` (the Amplify Console should set it automatically when the monorepo root is selected).
- `NEXT_PUBLIC_AUTH_PROVIDER=cognito`
- `COGNITO_DOMAIN`
- `COGNITO_APP_CLIENT_ID` (public app-client identifier; not an app-client secret)
- `COGNITO_REDIRECT_URI=https://<amplify-branch-host>/auth/callback`
- `COGNITO_SIGN_OUT_URI=https://<amplify-branch-host>/login`
- `COGNITO_LINK_API_URL` (the existing staging Lambda's Cognito link endpoint)
- `COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS`
- `NEXT_PUBLIC_SUPABASE_URL` (staging project only)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (browser-safe publishable/anon key only)
- `NEXT_PUBLIC_API_URL` (existing staging Lambda Function URL)

Never place Gemini, Qdrant, Supabase service-role, JWT signing, AWS credentials, or other backend secrets into Amplify frontend variables.

## Required follow-up after Amplify allocates its branch URL

These changes are deferred until the exact Amplify domain exists, so we do not guess the URL:
1. Update the **staging Cognito app client only**: add the Amplify `/auth/callback` URL to allowed callback URLs and the Amplify `/login` URL to allowed sign-out URLs. Preserve the existing Vercel URLs.
2. Create a reviewed CloudFormation change set for the existing `ewa-cognito-staging-api` stack, using the current image and all prior parameters via “Use previous value”; set the new optional `AdditionalFrontendOrigin` to the exact Amplify origin. The template keeps the existing Vercel origin and appends the Amplify origin for Lambda Function URL CORS.
3. Review the change set: the only expected resource update is the existing `StagingApi` in place (no replacement, no new Lambda or bucket resources). Production must stay untouched.
4. Test the Amplify domain: login, callback, session refresh, logout, direct navigation/page refresh, API calls, chatbot, job application/resume upload, and Employee-versus-Management access. Do not cut over or delete Vercel.
5. Leave the AWS branch isolated until those tests pass. Promote nothing to Production.

## Cost guardrails

Amplify Hosting is pay-as-you-go outside any eligible Free Tier: AWS currently lists standard builds at $0.01/build minute, CDN storage at $0.023/GB-month, data served at $0.15/GB, and SSR request/duration charges; the pricing page lists monthly free allowances where eligible. Do not add WAF ($15/month per app), custom domains, separate S3 buckets, CloudFront distributions, or other optional resources for this staging test. Watch AWS Billing after the first build and small smoke test.

## Current status

- [x] Inspected Next.js architecture; static-only S3 export is not compatible as-is.
- [x] Captured the existing READY Vercel preview URL and deployment ID as rollback reference.
- [x] Prepared Amplify SSR build config and an isolated AWS hosting branch.
- [x] Prepared an optional staging Lambda CORS parameter for an additional Amplify origin without removing Vercel.
- [ ] User creates the Amplify app / authorizes the GitHub connection in AWS Console (AWS resource creation cannot be executed through the connected GitHub/Vercel tools).
- [ ] Configure Amplify staging variables and Cognito callback/sign-out URLs after the branch URL is allocated.
- [ ] Update staging Lambda CORS through a reviewed change set.
- [ ] Run the live browser smoke test; keep Vercel intact.

