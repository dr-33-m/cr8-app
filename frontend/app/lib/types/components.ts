// General component interfaces
export interface ConfirmationItem {
  label: string;
  value: string;
  className?: string;
}

export interface ConfirmationCardProps {
  title: string;
  description: string;
  items: ConfirmationItem[];
  className?: string;
}

export interface ConnectionStatusProps {
  status: import("@/lib/types/websocket").WebSocketStatus;
}

export interface FormErrorProps {
  message?: string;
}

export interface Step {
  number: number;
  title: string;
}

export interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export interface ErrorComponentProps {
  message: string;
  action?: () => void;
  actionText?: string;
  actionIcon?: React.ReactNode;
  className?: string;
}

export interface EmptyStateProps {
  title?: string;
  description?: string;
  hint?: string;
  icon?: React.ReactNode;
  className?: string;
}
