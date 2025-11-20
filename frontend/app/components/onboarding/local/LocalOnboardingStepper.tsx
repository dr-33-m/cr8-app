import { useEffect, useState } from "react";
import useUserStore from "@/store/userStore";
import { OnboardingStepper, Stepper } from "./OnboardingStepper";
import { LoadingSpinner } from "@/components/placeholders/LoadingSpinner";

export function LocalOnboardingStepper() {
  const {
    username: storedUsername,
    selectedBlendFile: storedBlendFile,
    _hasHydrated,
  } = useUserStore();
  const [isHydrated, setIsHydrated] = useState(false);

  // Wait for store hydration before rendering stepper
  useEffect(() => {
    if (_hasHydrated) {
      setIsHydrated(true);
    }
  }, [_hasHydrated]);

  // Calculate initial step based on stored state
  const getInitialStep = () => {
    if (storedUsername && storedBlendFile) {
      return "launch";
    } else if (storedUsername) {
      return "folder";
    }
    return "username"; // default
  };

  // Show loading state while store is hydrating
  if (!isHydrated) {
    return <LoadingSpinner fullScreen message="Loading..." />;
  }

  return (
    <Stepper.Provider
      initialStep={getInitialStep()}
      className="min-h-screen flex items-center justify-center p-4"
    >
      <OnboardingStepper />
    </Stepper.Provider>
  );
}
