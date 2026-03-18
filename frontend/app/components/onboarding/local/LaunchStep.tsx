import { ConfirmationCard } from "@/components/confirmation-card";
import useUserStore from "@/store/userStore";
import { BlendFileInfo } from "@/lib/types/onboarding";

interface LaunchStepProps {
  folderPath: string;
  selectedBlendFile: BlendFileInfo | null;
}

export function LaunchStep({
  folderPath,
  selectedBlendFile,
}: LaunchStepProps) {
  const { username } = useUserStore();

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
