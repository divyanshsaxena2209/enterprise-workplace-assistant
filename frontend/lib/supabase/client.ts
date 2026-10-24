import { createBrowserClient } from '@supabase/ssr'
import { getCognitoAccessToken } from '@/lib/auth/cognito'

let client: ReturnType<typeof createBrowserClient> | undefined;

export function createClient() {
  if (client) return client;

  const options = process.env.NEXT_PUBLIC_AUTH_PROVIDER === 'cognito'
    ? { accessToken: getCognitoAccessToken }
    : undefined;

  client = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    options,
  );
  return client;
}
