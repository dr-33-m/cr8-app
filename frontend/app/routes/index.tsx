import { useState } from "react";
import { createFileRoute, useNavigate, getRouteApi } from "@tanstack/react-router";
import { LocalOnboardingStepper } from "@/components/onboarding/local";
import { NewProjectStepper } from "@/components/onboarding/NewProjectStepper";
import useUserStore from "@/store/userStore";
import useInboxStore from "@/store/inboxStore";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { signInFn } from "@/server/auth/functions";
import { InviteDialog } from "@/components/invite/InviteDialog";
import { BlendFileBrowser } from "@/components/blend-browser/BlendFileBrowser";
import type { BlendFile } from "@/server/api/storage/functions";
import { Lock } from "lucide-react";
import cr8 from "@/assets/cr8.jpeg";

const rootRoute = getRouteApi("__root__");

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
  const { userProfile } = rootRoute.useLoaderData();

  if (!auth.isAuthenticated) {
    return <SignInPage />;
  }

  const navigate = useNavigate();
  const { setSelectedBlendObject, setEmptyProject } = useUserStore();
  const [choice, setChoice] = useState<RemoteChoice>("none");
  const [isApproved, setIsApproved] = useState(
    userProfile?.is_approved ?? false
  );
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showBlendBrowser, setShowBlendBrowser] = useState(false);

  if (choice === "empty") {
    return <RemoteNewProjectLauncher onBack={() => setChoice("none")} />;
  }

  const handleNewProject = () => {
    if (isApproved) {
      setChoice("empty");
    } else {
      setShowInviteDialog(true);
    }
  };

  const handleOpenExisting = () => {
    if (isApproved) {
      setShowBlendBrowser(true);
    } else {
      setShowInviteDialog(true);
    }
  };

  const handleSelectBlendFile = (file: BlendFile) => {
    setEmptyProject(false);
    setSelectedBlendObject(file.filename, file.key);
    useInboxStore.getState().clearAll();
    navigate({ to: "/workspace" });
  };

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
            className="w-full h-20 flex flex-col items-center justify-center gap-1 relative"
            onClick={handleNewProject}
          >
            {!isApproved && (
              <Lock className="absolute top-3 right-3 h-4 w-4 text-muted-foreground" />
            )}
            <span className="text-base font-medium">New Empty Project</span>
            <span className="text-xs text-muted-foreground">
              {isApproved
                ? "Start with a fresh Blender scene"
                : "Requires invite token to unlock"}
            </span>
          </Button>
          <Button
            variant="outline"
            className="w-full h-20 flex flex-col items-center justify-center gap-1 relative"
            onClick={handleOpenExisting}
          >
            {!isApproved && (
              <Lock className="absolute top-3 right-3 h-4 w-4 text-muted-foreground" />
            )}
            <span className="text-base font-medium">
              Open Existing Project
            </span>
            <span className="text-xs text-muted-foreground">
              {isApproved
                ? "Browse your cloud blend files"
                : "Requires invite token to unlock"}
            </span>
          </Button>
        </CardContent>
      </Card>

      <BlendFileBrowser
        open={showBlendBrowser}
        onOpenChange={setShowBlendBrowser}
        accessToken={auth.accessToken!}
        onSelect={handleSelectBlendFile}
      />

      <InviteDialog
        open={showInviteDialog}
        onOpenChange={setShowInviteDialog}
        accessToken={auth.accessToken!}
        onSuccess={() => setIsApproved(true)}
      />
    </div>
  );
}

function RemoteNewProjectLauncher({ onBack }: { onBack: () => void }) {
  const navigate = useNavigate();
  const { auth } = Route.useRouteContext();
  const { setEmptyProject, clearBlendSelection } = useUserStore();
  const username = auth.isAuthenticated ? auth.user.name : "";

  const handleLaunch = () => {
    // Drop any previously selected cloud file, or its stale key would ride
    // along in the socket auth and open that file instead of an empty scene
    clearBlendSelection();
    setEmptyProject(true);
    useInboxStore.getState().clearAll();
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
