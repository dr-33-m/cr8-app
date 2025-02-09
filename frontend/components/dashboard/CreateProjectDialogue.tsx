import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { projectTypes, projectTemplates } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { StepIndicator } from "@/components/ui/step-indicator";
import { ProjectFormData } from "@/lib/types/ProjectConfig";
import { CircleAlert, LoaderPinwheel, Lock } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useNavigate } from "@tanstack/react-router";
import { useProjectStore } from "@/store/projectStore";
import { toast } from "sonner";
import { MoodboardData } from "@/lib/types/moodboard";
import useUserStore from "@/store/userStore";
import { useServerHealth } from "@/hooks/useServerHealth";

const c8_engine_server = import.meta.env.VITE_CR8_ENGINE_SERVER;

export function CreateProjectDialog() {
  const { serverStatus, isCheckingHealth, serverMessage, checkHealth } =
    useServerHealth();
  const userInfo = useUserStore((store) => store.userInfo);
  const logto_userId = userInfo?.sub;
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<ProjectFormData>({
    name: "",
    description: "",
    type: "",
    subtype: "",
    template: "",
    moodboard: "",
  });
  const [loading, setLoading] = useState(false);
  const steps = ["Project Details", "Type & Style", "Moodboard", "Template"];

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);
  const [moodboards, setMoodboards] = useState<MoodboardData[]>([]);
  const { setProjectName, setProjectTemplate } = useProjectStore();
  const navigate = useNavigate();

  const onSubmit = async () => {
    if (step === steps.length) {
      try {
        setLoading(true);

        // Prepare project data matching backend model
        const projectData = {
          name: formData.name,
          description: formData.description,
          project_type: formData.type,
          subtype: formData.subtype,
          project_status: "draft", // Default initial status
          template: formData.template,
          moodboard: formData.moodboard,
          logto_userId,
        };

        const response = await fetch(
          `${c8_engine_server}/api/v1/projects/create`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              // Add authentication headers if required
              // 'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(projectData),
          }
        );

        if (!response.ok) {
          throw new Error("Failed to create project");
        }

        const createdProject = await response.json();

        // Update Zustand store
        setProjectName(createdProject.name);
        setProjectTemplate(formData.template);

        toast.success("Project created successfully!");
        navigate({ to: `/project/${createdProject.id}` });
      } catch (error) {
        console.error("Project creation error:", error);
        toast.error("Failed to create project");
      } finally {
        setLoading(false);
      }
    }
    nextStep();
  };

  useEffect(() => {
    if (!logto_userId) {
      console.warn("No logto user ID found, skipping moodboard fetch.");
      return;
    }
    const fetchMoodboards = async () => {
      try {
        const response = await fetch(
          `${c8_engine_server}/api/v1/moodboards/list?logto_userId=${logto_userId}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch moodboards");
        }
        const data = await response.json();
        setMoodboards(data);
      } catch (error) {
        console.error("Moodboard fetch error:", error);
        toast.error("Failed to load moodboards");
      }
    };

    fetchMoodboards();
  }, [logto_userId]);

  // Handle server status changes
  useEffect(() => {
    if (!isCheckingHealth && serverStatus === "healthy") {
      setIsOpen(true);
    }
  }, [serverStatus, isCheckingHealth]);

  const isServerUnhealthy =
    isCheckingHealth || (serverStatus !== "healthy" && !isCheckingHealth);
  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <Label htmlFor="name">Project Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="Enter project name"
                className="bg-cr8-dark/20 border-cr8-charcoal/10"
              />
            </div>
            <div className="space-y-3">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Enter project description"
                className="bg-cr8-dark/20 border-cr8-charcoal/10 min-h-[100px]"
              />
            </div>
            <Button
              className="w-full bg-blue-600 hover:bg-blue-700"
              onClick={nextStep}
              disabled={!formData.name}
            >
              Next Step
            </Button>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <Label>Project Type</Label>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(projectTypes).map(
                  ([key, { icon: Icon, locked }]) => (
                    <button
                      key={key}
                      onClick={() => {
                        if (!locked) {
                          setFormData({ ...formData, type: key, subtype: "" });
                        }
                      }}
                      disabled={locked}
                      className={cn(
                        "p-4 rounded-lg border flex items-center gap-3 transition-all",
                        formData.type === key
                          ? "border-cr8-blue bg-cr8-blue/10"
                          : "border-cr8-charcoal/10 bg-cr8-dark/20 hover:bg-cr8-dark/30",
                        locked && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="capitalize">
                        {key.replace(/([A-Z])/g, " $1").trim()}
                      </span>
                      {locked && <Lock className="w-4 h-4 ml-auto" />}{" "}
                    </button>
                  )
                )}
              </div>
            </div>

            {formData.type && (
              <div className="space-y-3">
                <Label>Project Subtype</Label>
                <div className="grid grid-cols-3 gap-3">
                  {projectTypes[formData.type].subtypes.map((subtype) => (
                    <button
                      key={subtype}
                      onClick={() => setFormData({ ...formData, subtype })}
                      className={cn(
                        "p-3 rounded-lg border text-sm transition-all",
                        formData.subtype === subtype
                          ? "border-cr8-blue bg-cr8-blue/10"
                          : "border-cr8-charcoal/10 bg-cr8-dark/20 hover:bg-cr8-dark/30"
                      )}
                    >
                      {subtype}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={prevStep}>
                Back
              </Button>
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                onClick={nextStep}
                disabled={!formData.type || !formData.subtype}
              >
                Next Step
              </Button>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <Label>Select Moodboard</Label>
              {moodboards.length > 0 ? (
                <Select
                  value={formData.moodboard}
                  onValueChange={(value) => {
                    setFormData({ ...formData, moodboard: value });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a moodboard" />
                  </SelectTrigger>
                  <SelectContent>
                    {moodboards.map((moodboard, index) => (
                      <SelectItem key={index} value={moodboard?.name}>
                        <div>
                          <p className="font-medium">{moodboard?.name}</p>
                          <p className="text-sm text-gray-400">
                            {moodboard?.description}
                          </p>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Button
                  variant="outline"
                  className="w-full justify-start text-left h-auto p-4"
                  onClick={() => {
                    /* Open moodboard creation dialog */
                  }}
                >
                  <div>
                    <p className="font-medium">Create New Moodboard</p>
                    <p className="text-sm text-gray-400">
                      Start fresh with a new moodboard
                    </p>
                  </div>
                </Button>
              )}
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={prevStep}>
                Back
              </Button>
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                onClick={nextStep}
              >
                Next Step
              </Button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <Label>Select Template</Label>
              <div className="grid grid-cols-2 gap-4">
                {projectTemplates[formData.type]?.map((template) => (
                  <button
                    key={template.id}
                    onClick={() =>
                      setFormData({ ...formData, template: template.id })
                    }
                    className={cn(
                      "rounded-lg overflow-hidden transition-all",
                      formData.template === template.id
                        ? "ring-2 ring-cr8-blue"
                        : "ring-1 ring-cr8-charcoal/10 hover:ring-cr8-charcoal/30"
                    )}
                  >
                    <img
                      src={template.thumbnail}
                      alt={template.name}
                      className="w-full h-32 object-cover"
                    />
                    <div className="p-3 bg-black/40">
                      <p className="text-sm font-medium">{template.name}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={prevStep}>
                Back
              </Button>
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                disabled={!formData.template || loading}
                onClick={onSubmit}
              >
                {loading && <LoaderPinwheel className="w-5 h-5 animate-spin" />}
                {loading ? "Preparing Set..." : "Create Project"}
              </Button>
            </div>
          </div>
        );
    }
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (isServerUnhealthy) {
          return;
        }
        setIsOpen(open);
      }}
    >
      <DialogTrigger asChild>
        <div className="relative w-full">
          <Button
            size="lg"
            className="bg-cr8-blue hover:bg-cr8-blue/60 text-white w-full disabled:bg-gray-500"
            onClick={() => checkHealth()}
            disabled={isServerUnhealthy}
          >
            {isCheckingHealth
              ? "Checking Cr8 Engine..."
              : serverMessage.buttonText}
          </Button>
          {serverStatus !== "healthy" && serverMessage.message && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger className="absolute -top-7 inset-x-0 flex justify-center">
                  <CircleAlert className="h-5 w-5 text-yellow-500" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{serverMessage.message}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] bg-cr8-charcoal/95 backdrop-blur-xl border-white/10">
        {serverStatus !== "healthy" ? (
          <div className="p-6 text-center space-y-4">
            <h3 className="text-xl font-semibold">
              Cr8 Engine Is Unavailable{" "}
            </h3>
            <p className="text-yellow-500">{serverMessage.message}</p>
            <Button onClick={checkHealth}>Retry Connection</Button>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="text-xl font-semibold">
                Create New Project
              </DialogTitle>
            </DialogHeader>
            <StepIndicator steps={steps} currentStep={step} className="mb-6" />
            {renderStep()}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
