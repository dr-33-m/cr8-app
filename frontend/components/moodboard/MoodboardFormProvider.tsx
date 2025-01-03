import { FormProvider } from "react-hook-form";
import { useMoodboardForm } from "@/hooks/useMoodboardForm";
import { ReactNode } from "react";

interface MoodboardFormProviderProps {
  children: ReactNode;
}

export function MoodboardFormProvider({
  children,
}: MoodboardFormProviderProps) {
  const { form } = useMoodboardForm();

  return <FormProvider {...form}>{children}</FormProvider>;
}
