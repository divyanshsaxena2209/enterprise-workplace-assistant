import assert from "node:assert/strict";
import { test } from "node:test";

import { handler } from "./index.mjs";

test("adds the Supabase infrastructure role to Cognito ID and access tokens", async () => {
  const event = {
    response: {
      claimsAndScopeOverrideDetails: {
        accessTokenGeneration: {
          claimsToAddOrOverride: { custom_access_claim: "preserve-me" },
        },
        idTokenGeneration: {
          claimsToAddOrOverride: { custom_id_claim: "preserve-me-too" },
        },
      },
    },
  };

  const result = await handler(event);
  const claims = result.response.claimsAndScopeOverrideDetails;

  assert.equal(claims.accessTokenGeneration.claimsToAddOrOverride.role, "authenticated");
  assert.equal(claims.idTokenGeneration.claimsToAddOrOverride.role, "authenticated");
  assert.equal(claims.accessTokenGeneration.claimsToAddOrOverride.custom_access_claim, "preserve-me");
  assert.equal(claims.idTokenGeneration.claimsToAddOrOverride.custom_id_claim, "preserve-me-too");
});

test("does not grant application management privileges", async () => {
  const result = await handler({ response: {} });
  const claims = result.response.claimsAndScopeOverrideDetails;

  assert.equal(claims.accessTokenGeneration.claimsToAddOrOverride.role, "authenticated");
  assert.equal(claims.idTokenGeneration.claimsToAddOrOverride.role, "authenticated");
  assert.equal("application_role" in claims.accessTokenGeneration.claimsToAddOrOverride, false);
});
