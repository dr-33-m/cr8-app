import { createServerFn } from "@tanstack/react-start";

const engineUrl = process.env.API_URL || "http://localhost:8000";

/**
 * Sync the current user to the database (upsert).
 * Called from the root route loader after authentication.
 * Returns the user profile including is_approved status.
 */
export const syncUserFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: {
      accessToken: string;
      email: string | null;
      name: string;
      picture: string | null;
    }) => data
  )
  .handler(async ({ data }) => {
    const response = await fetch(`${engineUrl}/api/v1/users/sync`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${data.accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: data.email,
        name: data.name,
        picture: data.picture,
      }),
    });

    if (!response.ok) {
      throw new Error(`User sync failed: ${response.status}`);
    }

    return response.json();
  });
