import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LocalOnboardingStepper } from "@/components/onboarding/local";
import { NewProjectStepper } from "@/components/onboarding/NewProjectStepper";
import useUserStore from "@/store/userStore";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { signInFn } from "@/server/auth/functions";
import cr8 from "@/assets/cr8.jpeg";

const isRemoteMode = import.meta.env.VITE_LAUNCH_MODE === "remote";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  if (isRemoteMode) {
    return <RemoteHome />;
  }
  return <LocalHome />;
}

// ---------------------------------------------------------------------------
// Remote mode: Logto auth → project selection (New + Existing disabled)
// ---------------------------------------------------------------------------

type RemoteChoice = "none" | "empty";

function RemoteHome() {
  const { auth } = Route.useRouteContext();

  if (!auth.isAuthenticated) {
    return <SignInPage />;
  }

  const [choice, setChoice] = useState<RemoteChoice>("none");

  if (choice === "empty") {
    return <RemoteNewProjectLauncher onBack={() => setChoice("none")} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle>Welcome to Cr8</CardTitle>
          <CardDescription>How would you like to start?</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            variant="outline"
            className="w-full h-20 flex flex-col items-center justify-center gap-1"
            onClick={() => setChoice("empty")}
          >
            <span className="text-base font-medium">New Empty Project</span>
            <span className="text-xs text-muted-foreground">
              Start with a fresh Blender scene
            </span>
          </Button>
          <Button
            variant="outline"
            className="w-full h-20 flex flex-col items-center justify-center gap-1 opacity-50 cursor-not-allowed"
            disabled
          >
            <span className="text-base font-medium">
              Open Existing Project
            </span>
            <span className="text-xs text-muted-foreground">
              Coming soon — browse your remote blend files
            </span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function RemoteNewProjectLauncher({ onBack }: { onBack: () => void }) {
  const navigate = useNavigate();
  const { auth } = Route.useRouteContext();
  const { setEmptyProject } = useUserStore();
  const username = auth.isAuthenticated ? auth.user.name : "";

  const handleLaunch = () => {
    setEmptyProject(true);
    navigate({ to: "/workspace" });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle>New Empty Project</CardTitle>
          <CardDescription>
            Launch Blender with a fresh default scene
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-lg border p-4 space-y-2">
            <p className="text-sm text-muted-foreground">Username</p>
            <p className="font-medium">{username}</p>
          </div>
          <div className="flex gap-3">
            <Button onClick={onBack} variant="outline" className="flex-1">
              Back
            </Button>
            <Button onClick={handleLaunch} className="flex-1">
              Launch Workspace
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Local mode: username/localStorage → project selection (New + Open Local)
// ---------------------------------------------------------------------------

type LocalChoice = "none" | "empty" | "local";

function LocalHome() {
  const { isEmptyProject, selectedBlendFile } = useUserStore();

  const getInitialChoice = (): LocalChoice => {
    if (isEmptyProject) return "empty";
    if (selectedBlendFile) return "local";
    return "none";
  };

  const [choice, setChoice] = useState<LocalChoice>(getInitialChoice);

  if (choice === "local") {
    return <LocalOnboardingStepper />;
  }

  if (choice === "empty") {
    return <NewProjectStepper onBack={() => setChoice("none")} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle>Welcome to Cr8</CardTitle>
          <CardDescription>How would you like to start?</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            variant="outline"
            className="w-full h-20 flex flex-col items-center justify-center gap-1"
            onClick={() => setChoice("empty")}
          >
            <span className="text-base font-medium">New Empty Project</span>
            <span className="text-xs text-muted-foreground">
              Start with a fresh Blender scene
            </span>
          </Button>
          <Button
            variant="outline"
            className="w-full h-20 flex flex-col items-center justify-center gap-1"
            onClick={() => setChoice("local")}
          >
            <span className="text-base font-medium">Open Local Project</span>
            <span className="text-xs text-muted-foreground">
              Select an existing .blend file from your machine
            </span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sign-in page (remote mode only)
// ---------------------------------------------------------------------------

function SignInPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async () => {
    setIsLoading(true);
    try {
      const { redirectUrl } = await signInFn();
      window.location.href = redirectUrl;
    } catch {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <img
            src={cr8}
            alt="Cr8-xyz"
            className="w-16 h-16 rounded-md mx-auto"
          />
          <div>
            <CardTitle>Welcome to Cr8-xyz</CardTitle>
            <CardDescription>
              Sign in to start creating worlds
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <Button
            className="w-full"
            size="lg"
            onClick={handleSignIn}
            disabled={isLoading}
          >
            {isLoading ? "Redirecting..." : "Sign In"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
