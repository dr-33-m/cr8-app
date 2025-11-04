import { createFileRoute } from "@tanstack/react-router";
import useUserStore from "@/store/userStore";
import { OnboardingStepper, Stepper } from "@/components/onboarding/local";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  const { username: storedUsername, selectedBlendFile: storedBlendFile } =
    useUserStore();

  // Calculate initial step based on stored state
  const getInitialStep = () => {
    if (storedUsername && storedBlendFile) {
      return "launch";
    } else if (storedUsername) {
      return "folder";
    }
    return "username"; // default
  };

  return (
    <Stepper.Provider
      initialStep={getInitialStep()}
      className="min-h-screen flex items-center justify-center p-4"
    >
      <OnboardingStepper />
    </Stepper.Provider>
  );
}
