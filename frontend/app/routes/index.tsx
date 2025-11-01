import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { StepIndicator } from "@/components/ui/step-indicator";
import { Card } from "@/components/ui/card";
import { ConfirmationCard } from "@/components/ui/confirmation-card";
import useUserStore from "@/store/userStore";
import {
  blendFileService,
  BlendFileInfo,
} from "@/lib/services/blendFileService";
import { toast } from "sonner";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  const [currentStep, setCurrentStep] = useState(1);
  const [username, setUsername] = useState("");
  const [folderPath, setFolderPath] = useState("");
  const [blendFiles, setBlendFiles] = useState<BlendFileInfo[]>([]);
  const [selectedBlendFile, setSelectedBlendFile] =
    useState<BlendFileInfo | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isReturningUser, setIsReturningUser] = useState(false);

  const navigate = useNavigate();
  const {
    setUsername: setStoreUsername,
    setBlendFolder,
    setSelectedBlendFile: setStoreSelectedBlendFile,
    username: storedUsername,
    selectedBlendFile: storedBlendFile,
    blendFolderPath: storedFolderPath,
    clearBlendSelection,
  } = useUserStore();

  // Check if user has already completed setup and react to logout
  useEffect(() => {
    if (storedUsername && storedBlendFile) {
      // Set up returning user (both values present)
      setIsReturningUser(true);
      setCurrentStep(4);
      setUsername(storedUsername);
      if (storedFolderPath) {
        setFolderPath(storedFolderPath);
      }
      // Create a mock selected blend file for returning users
      setSelectedBlendFile({
        filename: storedBlendFile,
        full_path: "", // We'll use stored path if available
      });
    } else if (!storedUsername && !storedBlendFile) {
      // Reset everything when both are empty (logout)
      setCurrentStep(1);
      setUsername("");
      setFolderPath("");
      setBlendFiles([]);
      setSelectedBlendFile(null);
      setIsReturningUser(false);
    }
    // Do nothing if only one value is present (normal progression)
  }, [storedUsername, storedBlendFile, storedFolderPath]);

  const handleUsernameNext = () => {
    if (username.trim()) {
      setStoreUsername(username.trim());
      setCurrentStep(2);
    } else {
      toast.error("Please enter a username");
    }
  };

  const handleScanFolder = async () => {
    if (!folderPath.trim()) {
      toast.error("Please enter a folder path");
      return;
    }

    setIsScanning(true);
    try {
      const response = await blendFileService.scanBlendFolder(
        folderPath.trim()
      );

      if (response.total_count === 0) {
        toast.warning("No .blend files found in the specified folder");
        setBlendFiles([]);
      } else {
        setBlendFiles(response.blend_files);
        setBlendFolder(folderPath.trim());
        setCurrentStep(3);
        toast.success(`Found ${response.total_count} blend file(s)`);
      }
    } catch (error) {
      // Error is already handled in the service with toast
      console.error("Error scanning folder:", error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileSelect = (file: BlendFileInfo) => {
    setSelectedBlendFile(file);
    setStoreSelectedBlendFile(file.filename, file.full_path);
    setCurrentStep(4);
  };

  const handleLaunchWorkspace = () => {
    if (selectedBlendFile) {
      navigate({ to: "/workspace" });
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const steps = [
    { number: 1, title: "Username" },
    { number: 2, title: "Blend Folder" },
    { number: 3, title: "Select File" },
    { number: 4, title: "Launch" },
  ];

  return (
    <div className="min-h-screen bg-linear-to-br from-[#2C2C2C] to-[#1C1C1C] text-white flex items-center justify-center p-4">
      <div className="w-full max-w-lg p-8 space-y-6 bg-cr8-charcoal/20 rounded-lg shadow-lg border border-white/10">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Welcome to Cr8</h1>
          <p className="text-gray-400">Set up your workspace</p>
        </div>

        {currentStep < 4 && (
          <StepIndicator steps={steps} currentStep={currentStep} />
        )}

        <div className="space-y-6">
          {/* Step 1: Username */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold mb-2">Enter Username</h3>
                <p className="text-gray-400 text-sm">
                  Choose a username for your session
                </p>
              </div>
              <Input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-transparent border-white/20"
                onKeyPress={(e) => e.key === "Enter" && handleUsernameNext()}
              />
              <Button
                onClick={handleUsernameNext}
                className="w-full bg-[#0077B6] hover:bg-[#005A8D]"
                disabled={!username.trim()}
              >
                Next
              </Button>
            </div>
          )}

          {/* Step 2: Folder Path */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold mb-2">
                  Blend Files Folder
                </h3>
                <p className="text-gray-400 text-sm">
                  Enter the path to your .blend files folder
                </p>
              </div>
              <Input
                type="text"
                placeholder="/path/to/your/blend/files"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                className="bg-transparent border-white/20"
                onKeyPress={(e) => e.key === "Enter" && handleScanFolder()}
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleBack}
                  variant="outline"
                  className="flex-1"
                >
                  Back
                </Button>
                <Button
                  onClick={handleScanFolder}
                  className="flex-1 bg-[#0077B6] hover:bg-[#005A8D]"
                  disabled={!folderPath.trim() || isScanning}
                >
                  {isScanning ? "Scanning..." : "Scan Folder"}
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: File Selection */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold mb-2">
                  Select Blend File
                </h3>
                <p className="text-gray-400 text-sm">
                  Choose a .blend file to open
                </p>
              </div>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {blendFiles.map((file, index) => (
                  <Card
                    key={index}
                    className="p-3 cursor-pointer hover:bg-white/5 border-white/10 transition-colors"
                    onClick={() => handleFileSelect(file)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{file.filename}</p>
                        <p className="text-xs text-gray-400 truncate">
                          {file.full_path}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
              <Button onClick={handleBack} variant="outline" className="w-full">
                Back
              </Button>
            </div>
          )}

          {/* Step 4: Confirmation */}
          {currentStep === 4 && selectedBlendFile && (
            <div className="space-y-4">
              <ConfirmationCard
                title="Ready to Launch"
                description="Confirm your selection and launch the workspace"
                items={[
                  { label: "Username", value: username },
                  { label: "Folder", value: folderPath, className: "text-sm" },
                  { label: "File", value: selectedBlendFile.filename },
                ]}
              />
              <div className="flex gap-3">
                {isReturningUser ? (
                  <>
                    <Button
                      onClick={() => {
                        clearBlendSelection();
                        setIsReturningUser(false);
                        setCurrentStep(2); // Go to folder selection, keep username
                        // Keep username from store, don't clear it
                        setFolderPath("");
                        setBlendFiles([]);
                        setSelectedBlendFile(null);
                      }}
                      variant="outline"
                      className="flex-1"
                    >
                      New Setup
                    </Button>
                    <Button
                      onClick={handleLaunchWorkspace}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      Launch Workspace
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      onClick={handleBack}
                      variant="outline"
                      className="flex-1"
                    >
                      Back
                    </Button>
                    <Button
                      onClick={handleLaunchWorkspace}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      Launch Workspace
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
