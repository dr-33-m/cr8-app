import { useNavigate } from "@tanstack/react-router";
import useUserStore from "@/store/userStore";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { toast } from "sonner";

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
   * - Navigating to home page
   */
  public async performLogout(): Promise<void> {
    try {
      // Reset all Zustand stores
      this.resetStores();

      // Clear any additional localStorage entries
      this.clearLocalStorage();

      // Disconnect any active WebSocket connections
      await this.disconnectWebSockets();

      // Navigate to home page
      this.navigateToHome();

      // Show success message
      toast.success("Successfully logged out");
    } catch (error) {
      console.error("Error during logout:", error);
      toast.error("Error during logout. Please refresh the page.");
    }
  }

  /**
   * Reset all Zustand stores to their initial state
   */
  private resetStores(): void {
    // Reset User Store
    useUserStore.getState().reset();

    // Reset Visibility Store
    useVisibilityStore.getState().reset();
  }

  /**
   * Clear any additional localStorage entries that might not be handled by Zustand
   */
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

  /**
   * Disconnect any active WebSocket connections
   */
  private async disconnectWebSockets(): Promise<void> {
    // WebSocket is now only available in workspace context
    // Disconnection happens automatically when navigating away from workspace
    // We can still dispatch the event for any cleanup listeners
    window.dispatchEvent(new CustomEvent("logout-disconnect"));
  }

  /**
   * Navigate to home page
   */
  private navigateToHome(): void {
    // Since we can't use useNavigate hook in a class, we'll use window.location
    // or emit an event that components can listen to
    window.location.href = "/";
  }
}

/**
 * Hook-based logout function for use in React components
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

      // Navigate to home
      navigate({ to: "/" });

      // Show success message
      toast.success("Successfully logged out");
    } catch (error) {
      console.error("Error during logout:", error);
      toast.error("Error during logout. Please refresh the page.");
    }
  };

  return logout;
};
