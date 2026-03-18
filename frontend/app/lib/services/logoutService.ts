import useUserStore from "@/store/userStore";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { toast } from "sonner";
import { signOutFn } from "@/server/auth/functions";
import { useNavigate } from "@tanstack/react-router";

const isRemoteMode = import.meta.env.VITE_LAUNCH_MODE === "remote";

/**
 * Comprehensive logout service that clears all persisted states
 * and handles proper session cleanup
 */
export class LogoutService {
  private static instance: LogoutService;

  private constructor() {}

  public static getInstance(): LogoutService {
    if (!LogoutService.instance) {
      LogoutService.instance = new LogoutService();
    }
    return LogoutService.instance;
  }

  /**
   * Performs complete logout including:
   * - Resetting all Zustand stores
   * - Clearing localStorage entries
   * - Disconnecting WebSocket connections
   * - Redirecting (Logto sign-out in remote mode, navigate home in local mode)
   *
   * Note: For local mode, use the useLogout hook instead (it has access to navigate).
   */
  public async performLogout(): Promise<void> {
    try {
      this.resetStores();
      this.clearLocalStorage();
      await this.disconnectWebSockets();

      if (isRemoteMode) {
        const { redirectUrl } = await signOutFn();
        window.location.href = redirectUrl;
      }
      // In local mode, caller is responsible for navigation
    } catch (error) {
      console.error("Error during logout:", error);
      toast.error("Error during logout. Please refresh the page.");
    }
  }

  private resetStores(): void {
    useUserStore.getState().reset();
    useVisibilityStore.getState().reset();
  }

  private clearLocalStorage(): void {
    const keysToRemove = ["user-storage"];
    keysToRemove.forEach((key) => {
      try {
        localStorage.removeItem(key);
      } catch (error) {
        console.warn(`Failed to remove localStorage key: ${key}`, error);
      }
    });
  }

  private async disconnectWebSockets(): Promise<void> {
    window.dispatchEvent(new CustomEvent("logout-disconnect"));
  }
}

/**
 * Hook-based logout function for use in React components.
 * Clears local state, then either redirects to Logto sign-out (remote)
 * or navigates home (local).
 */
export const useLogout = () => {
  const navigate = useNavigate();

  const logout = async () => {
    try {
      // Reset all Zustand stores
      useUserStore.getState().reset();
      useVisibilityStore.getState().reset();

      // Clear localStorage entries
      const keysToRemove = ["user-storage"];
      keysToRemove.forEach((key) => {
        try {
          localStorage.removeItem(key);
        } catch (error) {
          console.warn(`Failed to remove localStorage key: ${key}`, error);
        }
      });

      // Disconnect WebSocket connections
      window.dispatchEvent(new CustomEvent("logout-disconnect"));

      if (isRemoteMode) {
        // Redirect to Logto sign-out (clears server session + Logto session)
        await signOutFn();
      } else {
        // Local mode: navigate home (stores already cleared)
        navigate({ to: "/" });
      }
    } catch (error) {
      // signOutFn throws a redirect on success — only real errors reach here
      console.error("Error during logout:", error);
      toast.error("Error during logout. Please refresh the page.");
    }
  };

  return logout;
};
