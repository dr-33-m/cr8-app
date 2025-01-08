import { isBrowser } from "@/lib/utils";
import useUserStore from "@/store/userStore";
import {
  type IdTokenClaims,
  useHandleSignInCallback,
  useLogto,
} from "@logto/react";
import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AuthLoadingSteps, Step } from "@/components/AuthLoadingSteps";
import { nanoid } from "nanoid"; // New import for generating unique IDs

const cr8_engine_server = import.meta.env.VITE_CR8_ENGINE_SERVER;

export function Callback() {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const setUserInfoInStore = useUserStore((store) => store.setUserInfo);
  const logto = isBrowser ? useLogto() : null;
  const [userInfo, setUserInfo] = useState<IdTokenClaims | null>(null);
  const [steps, setSteps] = useState<Step[]>([
    { label: "Authenticating", status: "pending" },
    { label: "Fetching user information", status: "pending" },
    { label: "Checking user existence", status: "pending" },
    { label: "Saving user data", status: "pending" },
  ]);
  const uniqueString = nanoid(10); // Generate a unique string using nanoid
  const updateStep = (
    index: number,
    status: "pending" | "loading" | "complete"
  ) => {
    setSteps((prevSteps) =>
      prevSteps.map((step, i) => (i === index ? { ...step, status } : step))
    );
  };

  const fetchAndSetUserInfo = async () => {
    updateStep(1, "loading");
    try {
      const info = await logto?.getIdTokenClaims();
      if (info) {
        setUserInfo(info);
        setUserInfoInStore(info);
        updateStep(1, "complete");
        return info;
      }
    } catch (error) {
      console.error("Error fetching user info:", error);
    }
    return null;
  };

  const checkIfUserExists = async (logtoId: string) => {
    updateStep(2, "loading");
    try {
      const response = await fetch(
        `${cr8_engine_server}/api/v1/users/check/${logtoId}`
      );
      console.log("Check response:", response.status);
      updateStep(2, "complete");
      return response.status === 200;
    } catch (error) {
      console.error("Error checking user existence:", error);
      return false;
    }
  };

  const saveUserToDb = async (info: IdTokenClaims) => {
    if (!info.username || !info.sub) {
      console.error("Missing required user info:", info);
      return;
    }

    setIsProcessing(true);
    updateStep(3, "loading");

    try {
      const userExists = await checkIfUserExists(info.sub);

      if (userExists) {
        updateStep(3, "complete");
        navigate({ to: "/" });
        return;
      }

      const userPayload = {
        email: `${uniqueString}@example.com`,
        username: info.username,
        logto_id: info.sub,
      };

      const response = await fetch(
        `${cr8_engine_server}/api/v1/users/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(userPayload),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to register user");
      }
      updateStep(3, "complete");
    } catch (error) {
      console.error("Error in user registration flow:", error);
    } finally {
      setIsProcessing(false);
      navigate({ to: "/" });
    }
  };

  useEffect(() => {
    if (userInfo) {
      saveUserToDb(userInfo);
    }
  }, [userInfo]);

  // Only run in browser environment
  if (isBrowser) {
    const { isLoading } = useHandleSignInCallback(async () => {
      updateStep(0, "loading");
      await fetchAndSetUserInfo();
      updateStep(0, "complete");
    });

    if (isLoading || isProcessing) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-4">
          <h1 className="text-3xl font-bold mb-6">Setting Up Your Account</h1>
          <div className="bg-white/10 rounded-lg p-6 mb-8">
            <AuthLoadingSteps steps={steps} />
          </div>
          <p className="text-lg text-white/70 text-center max-w-md">
            Please wait while we prepare your dashboard. This may take a few
            moments.
          </p>
        </div>
      );
    }
  }

  return null;
}
