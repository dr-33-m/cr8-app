import { Button } from "@/components/ui/button";

interface ErrorComponentProps {
  message: string;
  action?: () => void;
  actionText?: string;
  actionIcon?: React.ReactNode;
  className?: string;
}

export function ErrorComponent({
  message,
  action,
  actionText = "Retry",
  actionIcon,
  className = "",
}: ErrorComponentProps) {
  return (
    <div className={`text-center py-4 ${className}`}>
      <p className="text-red-400 text-sm mb-2">{message}</p>
      {action && (
        <Button variant="outline" size="sm" onClick={action}>
          {actionIcon}
          {actionText}
        </Button>
      )}
    </div>
  );
}
