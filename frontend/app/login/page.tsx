"use client";

import CognitoLoginPage from "@/components/auth/CognitoLoginPage";

export default function LoginPage() {
  // Authentication is intentionally Cognito-only on the staging app.
  return <CognitoLoginPage />;
}
