import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useMoodboardStore } from "@/store/moodboardStore";
import { MoodboardFormData, moodboardSchema } from "@/lib/types/moodboard";

export function useMoodboardForm() {
  const { moodboard, updateMoodboard } = useMoodboardStore();

  const form = useForm<MoodboardFormData>({
    resolver: zodResolver(moodboardSchema),
    defaultValues: moodboard,
  });

  // Sync form changes to Zustand store
  useEffect(() => {
    const subscription = form.watch((value) => {
      updateMoodboard(value as Partial<MoodboardFormData>);
    });
    return () => subscription.unsubscribe();
  }, [form.watch, updateMoodboard]);

  return {
    form,
  };
}
