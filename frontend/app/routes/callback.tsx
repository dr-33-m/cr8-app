import { Callback } from "@/app/pages/Callback";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/callback")({
  component: Callback,
});
