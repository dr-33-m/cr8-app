import { createFileRoute } from "@tanstack/react-router";
import { handleCallbackFn } from "@/server/auth/functions";

const baseUrl = process.env.APP_BASE_URL || "https://studio.cr8-xyz.art";

export const Route = createFileRoute("/auth/callback")({
  loader: async ({ location }) => {
    const fullUrl = `${baseUrl}${location.href}`;
    await handleCallbackFn({ data: { callbackUrl: fullUrl } });
  },
  component: CallbackPage,
});

function CallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-muted-foreground">Signing in...</p>
    </div>
  );
}
