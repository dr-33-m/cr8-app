import { createServerFn } from "@tanstack/react-start";
import { redirect } from "@tanstack/react-router";
import { createLogtoClient } from "./logto";
import { useLogtoSession } from "./session";

const baseUrl = process.env.APP_BASE_URL || "https://studio.cr8-xyz.art";

/**
 * Trigger OIDC sign-in flow. Returns the Logto sign-in URL
 * for the client to redirect to (external redirect — leaves the app).
 */
export const signInFn = createServerFn({ method: "POST" }).handler(
  async () => {
    const { client, getNavigateUrl } = await createLogtoClient();
    await client.signIn(`${baseUrl}/auth/callback`);
    return { redirectUrl: getNavigateUrl() };
  }
);

/**
 * Handle the OIDC callback. Exchanges the auth code for tokens
 * and stores them in the HTTP-only session cookie.
 * Called from a route loader so throw redirect works here.
 */
export const handleCallbackFn = createServerFn({ method: "GET" })
  .inputValidator((data: { callbackUrl: string }) => data)
  .handler(async ({ data }) => {
    const { client } = await createLogtoClient();
    await client.handleSignInCallback(data.callbackUrl);
    throw redirect({ to: "/" });
  });

/**
 * Sign out. Returns the Logto sign-out URL
 * for the client to redirect to (external redirect — leaves the app).
 */
export const signOutFn = createServerFn({ method: "POST" }).handler(
  async () => {
    try {
      const { client, getNavigateUrl } = await createLogtoClient();
      await client.signOut(`${baseUrl}/`);
      const session = await useLogtoSession();
      await session.clear();
      return { redirectUrl: getNavigateUrl() };
    } catch (error) {
      console.error("Failed to sign out:", error);
      const session = await useLogtoSession();
      await session.clear();
      return { redirectUrl: `${baseUrl}/` };
    }
  }
);

/**
 * Get the current authentication context. Called in route loaders
 * to provide auth state during SSR and client navigation.
 */
export const getAuthContextFn = createServerFn({ method: "GET" }).handler(
  async () => {
    const { client } = await createLogtoClient();
    const context = await client.getContext({
      getAccessToken: !!process.env.LOGTO_API_RESOURCE,
      resource: process.env.LOGTO_API_RESOURCE,
      fetchUserInfo: false,
    });

    if (!context.isAuthenticated) {
      return {
        isAuthenticated: false as const,
        user: null,
        accessToken: null,
      };
    }

    const claims = context.claims;
    return {
      isAuthenticated: true as const,
      user: {
        id: claims?.sub ?? "",
        name:
          claims?.name ??
          claims?.username ??
          claims?.email ??
          "User",
        email: claims?.email ?? null,
        picture: claims?.picture ?? null,
      },
      accessToken: context.accessToken ?? null,
    };
  }
);

/**
 * Get a fresh access token for the cr8 API resource.
 * Called before Socket.IO connect/reconnect to pass JWT in auth.
 */
export const getAccessTokenFn = createServerFn({ method: "GET" }).handler(
  async () => {
    const { client } = await createLogtoClient();

    if (!process.env.LOGTO_API_RESOURCE) {
      return { token: null };
    }

    try {
      const token = await client.getAccessToken(
        process.env.LOGTO_API_RESOURCE
      );
      return { token: token ?? null };
    } catch {
      return { token: null };
    }
  }
);
