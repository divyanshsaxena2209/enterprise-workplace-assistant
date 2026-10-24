/**
 * Cognito Pre Token Generation trigger (event version V2_0).
 *
 * Supabase Third-Party Auth requires role=authenticated on Cognito JWTs so
 * Supabase Data API/Storage/Realtime use the authenticated Postgres role.
 * This function never assigns application roles such as MANAGEMENT.
 */
export const handler = async (event) => {
  const existing = event.response?.claimsAndScopeOverrideDetails ?? {};
  const accessTokenGeneration = existing.accessTokenGeneration ?? {};
  const idTokenGeneration = existing.idTokenGeneration ?? {};

  event.response = {
    ...(event.response ?? {}),
    claimsAndScopeOverrideDetails: {
      ...existing,
      accessTokenGeneration: {
        ...accessTokenGeneration,
        claimsToAddOrOverride: {
          ...(accessTokenGeneration.claimsToAddOrOverride ?? {}),
          role: "authenticated",
        },
      },
      idTokenGeneration: {
        ...idTokenGeneration,
        claimsToAddOrOverride: {
          ...(idTokenGeneration.claimsToAddOrOverride ?? {}),
          role: "authenticated",
        },
      },
    },
  };

  return event;
};
