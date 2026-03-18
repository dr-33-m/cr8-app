import { useSession } from "@tanstack/react-start/server";

const sessionConfig = {
  password: process.env.LOGTO_COOKIE_SECRET!,
  name: "logto-session",
  maxAge: 14 * 24 * 60 * 60, // 14 days
  cookie: {
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    httpOnly: true,
    path: "/",
  },
};

export function useLogtoSession() {
  return useSession<Record<string, string>>(sessionConfig);
}
