import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { ConfirmationCard } from "@/components/confirmation-card";
import { defineStepper } from "@/components/stepper";
import useUserStore from "@/store/userStore";
import {
  blendFileService,
  BlendFileInfo,
} from "@/lib/services/blendFileService";
import { toast } from "sonner";

export const Route = createFileRoute("/")({
  component: Home,
});

const { Stepper, useStepper } = defineStepper(
  { id: "username", title: "Username" },
  { id: "folder", title: "Blend Folder" },
  { id: "file", title: "Select File" },
  { id: "launch", title: "Launch" }
);

function Home() {
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

  const methods = useStepper();

  // Check if user has already completed setup and react to logout
  useEffect(() => {
    if (storedUsername && storedBlendFile) {
      // Set up returning user (both values present)
      setIsReturningUser(true);
      setUsername(storedUsername);
      if (storedFolderPath) {
        setFolderPath(storedFolderPath);
      }
      // Create a mock selected blend file for returning users
      setSelectedBlendFile({
        filename: storedBlendFile,
        full_path: "", // We'll use stored path if available
      });
      methods.goTo("launch");
    } else if (!storedUsername && !storedBlendFile) {
      // Reset everything when both are empty (logout)
      setUsername("");
      setFolderPath("");
      setBlendFiles([]);
      setSelectedBlendFile(null);
      setIsReturningUser(false);
      methods.goTo("username");
    }
    // Do nothing if only one value is present (normal progression)
  }, [storedUsername, storedBlendFile, storedFolderPath, methods]);

  const handleUsernameNext = () => {
    if (username.trim()) {
      setStoreUsername(username.trim());
      methods.next();
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
        methods.next();
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
    methods.next();
  };

  const handleLaunchWorkspace = () => {
    if (selectedBlendFile) {
      navigate({ to: "/workspace" });
    }
  };

  return (
    <Stepper.Provider className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle>Welcome to Cr8</CardTitle>
          <CardDescription>Set up your workspace</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <Stepper.Navigation>
            {methods.all.map((step) => (
              <Stepper.Step
                key={step.id}
                of={step.id}
                onClick={() => methods.goTo(step.id)}
              >
                <Stepper.Title>{step.title}</Stepper.Title>
              </Stepper.Step>
            ))}
          </Stepper.Navigation>

          <Stepper.Panel>
            {methods.switch({
              username: () => (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-2 text-foreground">
                      Enter Username
                    </h3>
                    <p className="text-muted-foreground text-sm">
                      Choose a username for your session
                    </p>
                  </div>
                  <Input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onKeyPress={(e) =>
                      e.key === "Enter" && !methods.isLast && methods.next()
                    }
                  />
                </div>
              ),
              folder: () => (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-2 text-foreground">
                      Blend Files Folder
                    </h3>
                    <p className="text-muted-foreground text-sm">
                      Enter the path to your .blend files folder
                    </p>
                  </div>
                  <Input
                    type="text"
                    placeholder="/path/to/your/blend/files"
                    value={folderPath}
                    onChange={(e) => setFolderPath(e.target.value)}
                    onKeyPress={(e) =>
                      e.key === "Enter" && !methods.isLast && methods.next()
                    }
                  />
                </div>
              ),
              file: () => (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-2 text-foreground">
                      Select Blend File
                    </h3>
                    <p className="text-muted-foreground text-sm">
                      Choose a .blend file to open
                    </p>
                  </div>
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {blendFiles.map((file, index) => (
                      <Card
                        key={index}
                        className="p-3 cursor-pointer hover:bg-accent transition-colors"
                        onClick={() => handleFileSelect(file)}
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-foreground">
                              {file.filename}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {file.full_path}
                            </p>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              ),
              launch: () => (
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
                  {isScanning ? "Scanning..." : "Scan Folder"}
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
                      onClick={() => {
                        clearBlendSelection();
                        setIsReturningUser(false);
                        methods.goTo("folder");
                        setFolderPath("");
                        setBlendFiles([]);
                        setSelectedBlendFile(null);
                      }}
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
    </Stepper.Provider>
  );
}
