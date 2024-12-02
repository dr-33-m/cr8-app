import { isBrowser } from "@/lib/utils";
import { useHandleSignInCallback } from "@logto/react";
import { useNavigate } from "@tanstack/react-router";

export function Callback() {
  const navigate = useNavigate();
  // FIXME: This is a temporary solution until we have a proper way to handle authentication in the Server.
  if (isBrowser) {
    const { isLoading } = useHandleSignInCallback(() => {
      navigate({ to: "/" });
    });

    if (isLoading) {
      return <div>Redirecting...</div>;
    }
  }
  return null;
}
