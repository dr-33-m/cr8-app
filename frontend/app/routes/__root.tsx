import {
  Outlet,
  ScrollRestoration,
  createRootRoute,
} from "@tanstack/react-router";
import { Meta, Scripts } from "@tanstack/start";
import type { ReactNode } from "react";
import CSS from "@/styles/globals.css?url";
import Navbar from "@/components/Navbar";
import { Toaster } from "@/components/ui/sonner";

export const Route = createRootRoute({
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
        href: CSS,
      },
    ],
  }),
  component: RootComponent,
});

function RootComponent() {
  return (
    <RootDocument>
      <Outlet />
    </RootDocument>
  );
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html>
      <head>
        <Meta />
      </head>
      <body>
        <Navbar />
        {children}
        <Toaster richColors closeButton position="top-right" />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}
