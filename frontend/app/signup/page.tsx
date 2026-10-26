"use client";

import CognitoSignupForm from "@/components/auth/CognitoSignupForm";

export default function SignupPage() {
  // Account creation uses the same Cognito authentication flow as sign-in.
  return <CognitoSignupForm />;
}
