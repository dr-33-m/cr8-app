import { createFileRoute } from "@tanstack/react-router";
import { LocalOnboardingStepper } from "@/components/onboarding/local";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  return <LocalOnboardingStepper />;
}
