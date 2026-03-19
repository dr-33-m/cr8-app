/// <reference types="vite/client" />
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
} from "@tanstack/react-router";
import type { ReactNode } from "react";
import appCss from "@/styles/globals.css?url";
import Navbar from "@/components/Navbar";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "next-themes";
import type { QueryClient } from "@tanstack/react-query";
import { TanStackDevtools } from "@tanstack/react-devtools";
import { ReactQueryDevtoolsPanel } from "@tanstack/react-query-devtools";
import { TanStackRouterDevtoolsPanel } from "@tanstack/react-router-devtools";
import { getAuthContextFn } from "@/server/auth/functions";
import { syncUserFn } from "@/server/api/users/functions";
import type { AuthContext, UserProfile } from "@/lib/types/auth";
import { RouteLoader } from "@/components/placeholders/RouteLoader";

const isRemoteMode = import.meta.env.VITE_LAUNCH_MODE === "remote";

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()(
  {
    beforeLoad: async () => {
      // In local mode, skip Logto auth entirely — local uses username/localStorage
      if (!isRemoteMode) {
        const localAuth: AuthContext = {
          isAuthenticated: false,
          user: null,
          accessToken: null,
        };
        return { auth: localAuth };
      }
      const auth = await getAuthContextFn();
      return { auth };
    },
    loader: async ({ context: { auth } }) => {
      // Sync user to DB in remote mode (runs in parallel, non-blocking)
      if (!isRemoteMode || !auth.isAuthenticated || !auth.accessToken) {
        return { userProfile: null as UserProfile | null };
      }

      try {
        const userProfile = await syncUserFn({
          data: {
            accessToken: auth.accessToken,
            email: auth.user.email,
            name: auth.user.name,
            picture: auth.user.picture,
          },
        });
        return { userProfile: userProfile as UserProfile | null };
      } catch (e) {
        console.error("Failed to sync user:", e);
        return { userProfile: null as UserProfile | null };
      }
    },
    pendingComponent: () => (
      <RouteLoader title="Cr8-xyz" message="Setting things up..." />
    ),
    head: () => ({
      meta: [
        {
          charSet: "utf-8",
        },
        {
          name: "viewport",
          content: "width=device-width, initial-scale=1",
        },
        {
          title: "Cr8-xyz App",
        },
      ],
      links: [
        {
          rel: "stylesheet",
          href: appCss,
        },
      ],
    }),
    component: RootComponent,
  },
);

function RootComponent() {
  const { auth } = Route.useRouteContext();

  return (
    <RootDocument>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <Navbar auth={auth} />
        <Outlet />
        <Toaster position="top-right" />
      </ThemeProvider>
      <TanStackDevtools
        plugins={[
          {
            name: "TanStack Query",
            render: <ReactQueryDevtoolsPanel />,
          },
          {
            name: "TanStack Router",
            render: <TanStackRouterDevtoolsPanel />,
          },
        ]}
      />
    </RootDocument>
  );
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html suppressHydrationWarning>
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
