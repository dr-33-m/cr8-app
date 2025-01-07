import { BottomControls } from "@/components/BottomControls";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { MoodboardActions } from "@/components/moodboard/MoodboardActions";
import { MoodboardFlow } from "@/components/moodboard/moodboardFlow";
import { MoodboardFormProvider } from "@/components/moodboard/MoodboardFormProvider";
import { PreviewWindow } from "@/components/PreviewWindow";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/project/moodboard/$moodboardId")({
  component: RouteComponent,
});

function RouteComponent() {
  const { moodboardId } = Route.useParams();
  return (
    <MoodboardFormProvider>
      <div className="relative w-full h-screen bg-[#1C1C1C] text-white">
        <ControlsOverlay>
          <PreviewWindow>
            <MoodboardFlow />
          </PreviewWindow>
          <BottomControls>
            <MoodboardActions moodboardId={moodboardId} />
          </BottomControls>
        </ControlsOverlay>
      </div>
    </MoodboardFormProvider>
  );
}
