import LogtoClient from "@logto/node";
import { LogtoSessionStorage } from "./storage";
import { useLogtoSession } from "./session";

const logtoConfig = {
  endpoint: process.env.LOGTO_ENDPOINT!,
  appId: process.env.LOGTO_APP_ID!,
  appSecret: process.env.LOGTO_APP_SECRET!,
  scopes: ["openid", "profile", "email", "offline_access"],
  resources: process.env.LOGTO_API_RESOURCE
    ? [process.env.LOGTO_API_RESOURCE]
    : undefined,
};

/**
 * Creates a LogtoClient per request. All state lives in the HTTP-only
 * session cookie — the client itself is stateless.
 *
 * The `navigate` adapter captures the redirect URL so the caller can
 * throw a TanStack Router redirect after calling signIn/signOut.
 */
export async function createLogtoClient() {
  const session = await useLogtoSession();
  const storage = new LogtoSessionStorage(session);

  let navigateUrl = "";
  const client = new LogtoClient(logtoConfig, {
    storage,
    navigate: (url: string) => {
      navigateUrl = url;
    },
  });

  return { client, getNavigateUrl: () => navigateUrl };
}
