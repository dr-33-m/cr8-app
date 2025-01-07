import { CheckCircle, Circle, Loader2 } from "lucide-react";

export type Step = {
  label: string;
  status: "pending" | "loading" | "complete";
};

type LoadingStepsProps = {
  steps: Step[];
};

export function AuthLoadingSteps({ steps }: LoadingStepsProps) {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center space-x-3">
          {step.status === "pending" && (
            <Circle className="h-5 w-5 text-gray-400" />
          )}
          {step.status === "loading" && (
            <Loader2 className="h-5 w-5 text-cr8-blue animate-spin" />
          )}
          {step.status === "complete" && (
            <CheckCircle className="h-5 w-5 text-cr8-yellow" />
          )}
          <span
            className={`text-lg ${step.status === "complete" ? "text-cr8-yellow" : "text-gray-700"}`}
          >
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}
