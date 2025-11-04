import * as React from "react";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { ConfirmationCardProps } from "@/lib/types/components";

const ConfirmationCard = React.forwardRef<
  HTMLDivElement,
  ConfirmationCardProps
>(({ title, description, items, className, ...props }, ref) => (
  <div className="space-y-4" ref={ref} {...props}>
    <div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
    <Card className={cn("p-4", className)}>
      <div className="space-y-2">
        {items.map((item, index) => (
          <React.Fragment key={index}>
            <div className="flex justify-between">
              <span className="text-gray-400">{item.label}:</span>
              <span className={cn("text-right", item.className)}>
                {item.value}
              </span>
            </div>
            {index < items.length - 1 && <Separator />}
          </React.Fragment>
        ))}
      </div>
    </Card>
  </div>
));

ConfirmationCard.displayName = "ConfirmationCard";

export { ConfirmationCard };
