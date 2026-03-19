import { createServerFn } from "@tanstack/react-start";

const engineUrl = process.env.API_URL || "http://localhost:8000";

/**
 * Redeem an invite token to unlock project launching.
 * Returns { approved: true } on success.
 */
export const redeemInviteFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: {
      token: string;
      accessToken: string;
    }) => data
  )
  .handler(async ({ data }) => {
    const response = await fetch(`${engineUrl}/api/v1/invitations/redeem`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${data.accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token: data.token }),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Failed to redeem invite" }));
      throw new Error(
        errorData.detail || `Failed to redeem invite (${response.status})`
      );
    }

    return response.json();
  });
