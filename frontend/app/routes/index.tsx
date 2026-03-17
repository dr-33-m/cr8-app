import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
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

export const Route = createFileRoute("/")({
  component: Home,
});

type ProjectChoice = "none" | "empty" | "local";

function Home() {
  const { isEmptyProject, selectedBlendFile, username } = useUserStore();

  // If returning user with a previous selection, go directly to the right flow
  const getInitialChoice = (): ProjectChoice => {
    if (username && isEmptyProject) return "empty";
    if (username && selectedBlendFile) return "local";
    return "none";
  };

  const [choice, setChoice] = useState<ProjectChoice>(getInitialChoice);

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
