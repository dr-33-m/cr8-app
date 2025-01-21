import type { TemplateControls } from "@/types/templateControls";

export const areControlsAvailable = (
  controls: TemplateControls | null
): boolean => {
  if (!controls) return false;
  return (
    controls.cameras.length > 0 ||
    controls.lights.length > 0 ||
    controls.objects.length > 0
  );
};
