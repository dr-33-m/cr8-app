import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

export function StepIndicator({ currentStep, totalSteps }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center space-x-2 mb-6">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={cn(
            "h-2 rounded-full transition-all duration-300",
            index + 1 <= currentStep
              ? "w-8 bg-cr8-blue"
              : "w-2 bg-cr8-charcoal/20"
          )}
        />
      ))}
    </div>
  );
}
