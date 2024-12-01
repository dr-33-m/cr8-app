import { useHandleSignInCallback } from "@logto/react";
import { redirect } from "@tanstack/react-router";

export function Callback() {
  const logto =
    typeof window !== "undefined" ? useHandleSignInCallback() : null;

  if (logto?.isAuthenticated) {
    console.log("User is authenticated");
    // Redirect to root path when finished
    throw redirect({
      to: "/",
    });
  } // Navigate to root path when finished

  // If there is an error during the authentication process
  if (logto?.error) {
    console.error("Authentication failed:", logto.error);
    return <div>Error: {logto.error.message}</div>;
  }
  // When it's working in progress
  if (logto?.isLoading) {
    return <div>Redirecting...</div>;
  }

  return null;
}
