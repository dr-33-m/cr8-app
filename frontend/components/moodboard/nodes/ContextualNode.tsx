import { Building2, Users, Target } from "lucide-react";
import { Industry, MoodboardFormData, UsageIntent } from "@/types/moodboard";
import { BaseNode } from "./BaseNode";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FormError } from "@/components/ui/form-error";
import { useFormContext } from "react-hook-form";

const industries: Industry[] = [
  "fashion",
  "music",
  "real-estate",
  "tech",
  "entertainment",
  "custom",
];
const usageIntents: UsageIntent[] = [
  "product-launch",
  "music-video",
  "social-media",
  "commercial",
];

export function ContextualNode() {
  const {
    register,
    formState: { errors },
    setValue,
    watch,
  } = useFormContext<MoodboardFormData>();

  const industryValue = watch("industry");
  const usageIntentValue = watch("usageIntent");
  return (
    <BaseNode
      title="Contextual Elements"
      showSourceHandle
      showTargetHandle
      titleColor="text-cr8-pink"
    >
      <div className="space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="text-cr8-pink" size={20} />
            <Select
              value={industryValue}
              onValueChange={(value) => setValue("industry", value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select Industry" />
              </SelectTrigger>
              <SelectContent>
                {industries.map((industry) => (
                  <SelectItem key={industry} value={industry}>
                    {industry.charAt(0).toUpperCase() + industry.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <FormError message={errors.industry?.message as string} />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <Users className="text-cr8-pink" size={20} />
            <input
              {...register("targetAudience")}
              type="text"
              placeholder="Target audience..."
              className="flex-1 bg-cr8-dark/30 backdrop-blur-md text-white rounded-md p-2 text-sm border border-cr8-charcoal/50"
            />
          </div>
          <FormError message={errors.targetAudience?.message as string} />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <Target className="text-cr8-pink" size={20} />
            <Select
              value={usageIntentValue}
              onValueChange={(value) => setValue("usageIntent", value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select Usage Intent" />
              </SelectTrigger>
              <SelectContent>
                {usageIntents.map((intent) => (
                  <SelectItem key={intent} value={intent}>
                    {intent
                      .split("-")
                      .map(
                        (word) => word.charAt(0).toUpperCase() + word.slice(1)
                      )
                      .join(" ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <FormError message={errors.usageIntent?.message as string} />
        </div>
      </div>
    </BaseNode>
  );
}
