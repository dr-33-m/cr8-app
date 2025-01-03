import { BottomControls } from "@/components/BottomControls";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { MoodboardActions } from "@/components/moodboard/MoodboardActions";
import { MoodboardFlow } from "@/components/moodboard/moodboardFlow";
import { MoodboardFormProvider } from "@/components/moodboard/MoodboardFormProvider";
import { PreviewWindow } from "@/components/PreviewWindow";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/project/moodboard")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <MoodboardFormProvider>
      <div className="relative w-full h-screen bg-[#1C1C1C] text-white">
        <ControlsOverlay>
          <PreviewWindow>
            <MoodboardFlow />
          </PreviewWindow>
          <BottomControls>
            <MoodboardActions />
          </BottomControls>
        </ControlsOverlay>
      </div>
    </MoodboardFormProvider>
  );
}
