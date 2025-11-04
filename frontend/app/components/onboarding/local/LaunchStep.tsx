import { ConfirmationCard } from "@/components/confirmation-card";
import { LaunchStepProps } from "@/lib/types/onboarding";

export function LaunchStep({
  username,
  folderPath,
  selectedBlendFile,
}: LaunchStepProps) {
  return (
    <div className="space-y-4">
      {selectedBlendFile && (
        <ConfirmationCard
          title="Ready to Launch"
          description="Confirm your selection and launch the workspace"
          items={[
            { label: "Username", value: username },
            {
              label: "Folder",
              value: folderPath,
              className: "text-sm",
            },
            { label: "File", value: selectedBlendFile.filename },
          ]}
        />
      )}
    </div>
  );
}
