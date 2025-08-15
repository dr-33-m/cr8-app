import { cn } from "@/lib/utils";

interface Step {
  number: number;
  title: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export function StepIndicator({
  steps,
  currentStep,
  className,
}: StepIndicatorProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      {steps.map((step, index) => {
        const isActive = step.number === currentStep;
        const isCompleted = step.number < currentStep;
        const isLast = index === steps.length - 1;

        return (
          <div key={step.number} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                  {
                    "bg-[#0077B6] text-white": isActive,
                    "bg-green-600 text-white": isCompleted,
                    "bg-gray-600 text-gray-300": !isActive && !isCompleted,
                  }
                )}
              >
                {isCompleted ? "✓" : step.number}
              </div>
              <span
                className={cn("text-xs mt-1 transition-colors", {
                  "text-white": isActive,
                  "text-green-400": isCompleted,
                  "text-gray-400": !isActive && !isCompleted,
                })}
              >
                {step.title}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn("flex-1 h-0.5 mx-2 transition-colors", {
                  "bg-green-600": isCompleted,
                  "bg-gray-600": !isCompleted,
                })}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
