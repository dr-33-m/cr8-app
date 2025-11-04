import useUserStore from "@/store/userStore";
import { OnboardingStepper, Stepper } from "./OnboardingStepper";

export function LocalOnboardingStepper() {
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
