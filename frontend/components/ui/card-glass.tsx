import { cn } from "@/lib/utils";

interface CardGlassProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export function CardGlass({ children, className, ...props }: CardGlassProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-white/10",
        "bg-gradient-to-b from-cr8-charcoal/10 to-cr8-charcoal/5",
        "backdrop-blur-xl shadow-xl",
        "before:absolute before:inset-0",
        "before:bg-gradient-to-r before:from-transparent before:via-cr8-charcoal/5 before:to-transparent",
        "before:animate-glass-shine",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
