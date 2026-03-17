import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { defineStepper } from "@/components/stepper";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import { UsernameStep } from "./local/UsernameStep";
import { ConfirmationCard } from "@/components/confirmation-card";

const { Stepper, useStepper } = defineStepper(
  { id: "username", title: "Username" },
  { id: "launch", title: "Launch" }
);

function NewProjectStepperContent({ onBack }: { onBack: () => void }) {
  const navigate = useNavigate();
  const methods = useStepper();
  const {
    setUsername: setStoreUsername,
    setEmptyProject,
    username: storedUsername,
  } = useUserStore();

  const [username, setUsername] = useState(() => storedUsername || "");

  useEffect(() => {
    if (!storedUsername) {
      setUsername("");
      methods.goTo("username");
    }
  }, [storedUsername, methods]);

  const handleUsernameNext = () => {
    if (username.trim()) {
      setStoreUsername(username.trim());
      methods.next();
    } else {
      toast.error("Please enter a username");
    }
  };

  const handleLaunchWorkspace = () => {
    setEmptyProject(true);
    navigate({ to: "/workspace" });
  };

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <CardTitle>New Empty Project</CardTitle>
        <CardDescription>
          Launch Blender with a fresh default scene
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <Stepper.Navigation>
          {methods.all.map((step) => {
            const currentStepIndex = methods.all.findIndex(
              (s) => s.id === methods.current.id
            );
            const stepIndex = methods.all.findIndex((s) => s.id === step.id);
            const isInactive = stepIndex > currentStepIndex;

            return (
              <Stepper.Step
                key={step.id}
                of={step.id}
                onClick={!isInactive ? () => methods.goTo(step.id) : undefined}
              >
                <Stepper.Title>{step.title}</Stepper.Title>
              </Stepper.Step>
            );
          })}
        </Stepper.Navigation>

        <Stepper.Panel>
          {methods.switch({
            username: () => (
              <UsernameStep
                username={username}
                onUsernameChange={setUsername}
                onEnterPress={handleUsernameNext}
              />
            ),
            launch: () => (
              <ConfirmationCard
                title="Ready to Launch"
                description="A new Blender project will be created with the default scene"
                items={[{ label: "Username", value: username }]}
              />
            ),
          })}
        </Stepper.Panel>

        <Stepper.Controls>
          <div className="flex justify-between gap-4">
            {methods.current.id === "username" && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={onBack}
                  className="flex-1"
                >
                  Back
                </Button>
                <Button
                  onClick={handleUsernameNext}
                  className="flex-1"
                  disabled={!username.trim()}
                >
                  Next
                </Button>
              </>
            )}

            {methods.current.id === "launch" && (
              <div className="flex gap-3 flex-1">
                <Button
                  onClick={methods.prev}
                  variant="outline"
                  className="flex-1"
                >
                  Back
                </Button>
                <Button onClick={handleLaunchWorkspace} className="flex-1">
                  Launch Workspace
                </Button>
              </div>
            )}
          </div>
        </Stepper.Controls>
      </CardContent>
    </Card>
  );
}

export function NewProjectStepper({ onBack }: { onBack: () => void }) {
  const { username: storedUsername } = useUserStore();

  const getInitialStep = () => {
    if (storedUsername) return "launch";
    return "username";
  };

  return (
    <Stepper.Provider
      initialStep={getInitialStep()}
      className="min-h-screen flex items-center justify-center p-4"
    >
      <NewProjectStepperContent onBack={onBack} />
    </Stepper.Provider>
  );
}
