import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { defineStepper } from "@/components/stepper";
import useUserStore from "@/store/userStore";
import { BlendFileInfo } from "@/lib/types/onboarding";
import { toast } from "sonner";
import { scanBlendFolder } from "@/server/api/onboarding-local/scanBlendFolder";
import { UsernameStep } from "./UsernameStep";
import { FolderStep } from "./FolderStep";
import { FileStep } from "./FileStep";
import { LaunchStep } from "./LaunchStep";

const { Stepper, useStepper } = defineStepper(
  { id: "username", title: "Username" },
  { id: "folder", title: "Blend Folder" },
  { id: "file", title: "Select File" },
  { id: "launch", title: "Launch" }
);

export function OnboardingStepper() {
  const navigate = useNavigate();
  const methods = useStepper();
  const {
    setUsername: setStoreUsername,
    setBlendFolder,
    setSelectedBlendFile: setStoreSelectedBlendFile,
    username: storedUsername,
    selectedBlendFile: storedBlendFile,
    blendFolderPath: storedFolderPath,
    clearBlendSelection,
  } = useUserStore();

  // Initialize state directly from store using lazy initialization
  const [username, setUsername] = useState(() => storedUsername || "");
  const [folderPath, setFolderPath] = useState(() => storedFolderPath || "");
  const [selectedBlendFile, setSelectedBlendFile] =
    useState<BlendFileInfo | null>(() => {
      if (storedUsername && storedBlendFile) {
        return {
          filename: storedBlendFile,
          full_path: storedFolderPath || "",
        };
      }
      return null;
    });
  const [isReturningUser, setIsReturningUser] = useState(
    () => !!(storedUsername && storedBlendFile)
  );

  // Local state for folder scanning
  const [blendFiles, setBlendFiles] = useState<BlendFileInfo[]>([]);
  const [isScanning, setIsScanning] = useState(false);

  // Handle logout/reset (when stored data is cleared)
  useEffect(() => {
    if (!storedUsername && !storedBlendFile) {
      setUsername("");
      setFolderPath("");
      setSelectedBlendFile(null);
      setIsReturningUser(false);
      methods.goTo("username");
    }
  }, [storedUsername, storedBlendFile, methods]);

  const handleUsernameNext = () => {
    if (username.trim()) {
      setStoreUsername(username.trim());
      methods.next();
    } else {
      toast.error("Please enter a username");
    }
  };

  const handleScanFolder = async () => {
    // If already scanned successfully, navigate to next step
    if (!isScanning && blendFiles.length > 0) {
      methods.next();
      return;
    }

    // Validate folder path
    if (!folderPath.trim()) {
      toast.error("Please enter a folder path");
      return;
    }

    // Start scanning
    setIsScanning(true);
    try {
      const result = await scanBlendFolder({
        data: { folderPath: folderPath.trim() },
      });
      setBlendFiles(result.blend_files || []);
      setBlendFolder(folderPath.trim());
      // Auto-advance to file selection step
      methods.next();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to scan folder"
      );
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileSelect = (file: BlendFileInfo) => {
    setSelectedBlendFile(file);
    setStoreSelectedBlendFile(file.filename, file.full_path);
    methods.next();
  };

  const handleLaunchWorkspace = () => {
    if (selectedBlendFile) {
      navigate({ to: "/workspace" });
    }
  };

  const handleNewSetup = () => {
    clearBlendSelection();
    setIsReturningUser(false);
    methods.goTo("folder");
    setFolderPath("");
    setSelectedBlendFile(null);
  };

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <CardTitle>Welcome to Cr8</CardTitle>
        <CardDescription>Set up your workspace</CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <Stepper.Navigation>
          {methods.all.map((step) => {
            // Only allow clicking on current step or previous steps
            const currentStepIndex = methods.all.findIndex(
              (s) => s.id === methods.current.id
            );
            const stepIndex = methods.all.findIndex((s) => s.id === step.id);
            const isInactive = stepIndex > currentStepIndex;

            return (
              <Stepper.Step
                key={step.id}
                of={step.id}
                onClick={!isInactive ? () => methods.goTo(step.id) : undefined}
              >
                <Stepper.Title>{step.title}</Stepper.Title>
              </Stepper.Step>
            );
          })}
        </Stepper.Navigation>

        <Stepper.Panel>
          {methods.switch({
            username: () => (
              <UsernameStep
                username={username}
                onUsernameChange={setUsername}
                onEnterPress={handleUsernameNext}
              />
            ),
            folder: () => (
              <FolderStep
                folderPath={folderPath}
                onFolderPathChange={setFolderPath}
                onEnterPress={handleScanFolder}
              />
            ),
            file: () => (
              <FileStep
                blendFiles={blendFiles}
                onFileSelect={handleFileSelect}
              />
            ),
            launch: () => (
              <LaunchStep
                username={username}
                folderPath={folderPath}
                selectedBlendFile={selectedBlendFile}
              />
            ),
          })}
        </Stepper.Panel>

        <Stepper.Controls>
          <div className="flex justify-between gap-4">
            {/* Show generic Back button only for non-launch steps */}
            {!methods.isFirst && methods.current.id !== "launch" && (
              <Button
                type="button"
                variant="outline"
                onClick={methods.prev}
                className="flex-1"
              >
                Back
              </Button>
            )}

            {methods.current.id === "username" && (
              <Button
                onClick={handleUsernameNext}
                className="flex-1"
                disabled={!username.trim()}
              >
                Next
              </Button>
            )}

            {methods.current.id === "folder" && (
              <Button
                onClick={handleScanFolder}
                className="flex-1"
                disabled={!folderPath.trim() || isScanning}
              >
                {isScanning
                  ? "Scanning..."
                  : blendFiles.length > 0
                  ? "Next"
                  : "Scan Folder"}
              </Button>
            )}

            {methods.current.id === "file" && (
              <Button
                onClick={methods.next}
                className="flex-1"
                disabled={!selectedBlendFile}
              >
                Next
              </Button>
            )}

            {methods.current.id === "launch" && (
              <div className="flex gap-3 flex-1">
                {isReturningUser ? (
                  <Button
                    onClick={handleNewSetup}
                    variant="outline"
                    className="flex-1"
                  >
                    New Setup
                  </Button>
                ) : (
                  <Button
                    onClick={methods.prev}
                    variant="outline"
                    className="flex-1"
                  >
                    Back
                  </Button>
                )}
                <Button
                  onClick={handleLaunchWorkspace}
                  className="flex-1"
                  disabled={!selectedBlendFile}
                >
                  Launch Workspace
                </Button>
              </div>
            )}
          </div>
        </Stepper.Controls>
      </CardContent>
    </Card>
  );
}

export { Stepper, useStepper };
