import { KeyboardEvent, useState } from "react";
import { BookOpen, Tags, Palette, AlertCircle } from "lucide-react";
import { MoodboardFormData, Theme, Tone } from "@/lib/types/moodboard";
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

const themes: Theme[] = [
  "minimalist",
  "futuristic",
  "rustic",
  "industrial",
  "vibrant",
  "custom",
];
const tones: Tone[] = [
  "joyful",
  "melancholic",
  "energetic",
  "serene",
  "bold",
  "dreamy",
];

export function TextualNode() {
  const {
    register,
    formState: { errors },
    setValue,
    watch,
  } = useFormContext<MoodboardFormData>();
  const [keywordInput, setKeywordInput] = useState("");

  const themeValue = watch("theme");
  const toneValue = watch("tone");
  const keywords = watch("keywords") || [];

  const handleKeywordSubmit = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && keywordInput.trim()) {
      setValue("keywords", [...keywords, keywordInput.trim()]);
      setKeywordInput("");
    }
  };

  return (
    <BaseNode
      title="Textual Elements"
      showSourceHandle
      showTargetHandle
      titleColor="text-cr8-purple"
    >
      <div className="space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <Palette className="text-cr8-purple" size={20} />
            <Select
              value={themeValue}
              onValueChange={(value: Theme) =>
                setValue("theme", value, { shouldValidate: true })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select Theme" />
              </SelectTrigger>
              <SelectContent>
                {themes.map((theme) => (
                  <SelectItem key={theme} value={theme}>
                    {theme.charAt(0).toUpperCase() + theme.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <FormError message={errors.theme?.message as string} />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <BookOpen className="text-cr8-purple" size={20} />
            <textarea
              {...register("storyline")}
              placeholder="Enter storyline..."
              className="flex-1 bg-cr8-dark/30 backdrop-blur-md text-white rounded-md p-2 text-sm border border-cr8-charcoal/50"
              maxLength={300}
            />
          </div>
          <FormError message={errors.storyline?.message as string} />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <Tags className="text-cr8-purple" size={20} />
            <input
              type="text"
              placeholder="Add keywords..."
              className="flex-1 bg-cr8-dark/30 backdrop-blur-md text-white rounded-md p-2 text-sm border border-cr8-charcoal/50"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyPress={handleKeywordSubmit}
            />
          </div>
          {keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-cr8-dark/50 rounded-md text-sm"
                >
                  {keyword}
                </span>
              ))}
            </div>
          )}
          {keywordInput.length > 0 && (
            <div className="flex items-center gap-2 text-cr8-blue text-sm mt-1">
              <AlertCircle className="h-4 w-4" />
              <span>Press Enter to add Keyword</span>
            </div>
          )}
          <FormError message={errors.keywords?.message as string} />
        </div>

        <div>
          <Select
            value={toneValue}
            onValueChange={(value: Tone) =>
              setValue("tone", value, { shouldValidate: true })
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select Tone" />
            </SelectTrigger>
            <SelectContent>
              {tones.map((tone) => (
                <SelectItem key={tone} value={tone}>
                  {tone.charAt(0).toUpperCase() + tone.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormError message={errors.tone?.message as string} />
        </div>
      </div>
    </BaseNode>
  );
}
