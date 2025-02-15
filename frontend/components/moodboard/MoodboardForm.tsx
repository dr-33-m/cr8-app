import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { useNavigate } from "@tanstack/react-router";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import { useState } from "react";
import { LoaderPinwheel } from "lucide-react";

const cr8_engine_server = import.meta.env.VITE_CR8_ENGINE_SERVER;

// Define the form schema using zod
export const moodBoardFormSchema = z.object({
  name: z.string().min(1, "Moodboard name is required"),
  description: z.string().optional(),
});

export function MoodboardForm() {
  const navigate = useNavigate();
  const { userInfo } = useUserStore((store) => store);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize the form
  const form = useForm({
    resolver: zodResolver(moodBoardFormSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  // Handle form submission
  const onSubmit = async (values: z.infer<typeof moodBoardFormSchema>) => {
    try {
      setIsLoading(true);
      const logto_userId = userInfo?.sub;
      Object.assign(values, { logto_userId });
      const res = await fetch(
        `${cr8_engine_server}/api/v1/moodboards/create_moodboard`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(values),
        }
      );

      if (!res.ok) {
        toast.error("Failed to create moodboard");
        throw new Error("Failed to create moodboard");
      }
      const data = await res.json();
      navigate({ to: `/project/moodboard/${data.id}` });
      return res.json();
    } catch (error) {
      toast.error("Failed to create moodboard");
      console.error("Error creating moodboard:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium">
                Moodboard Name
              </FormLabel>
              <FormControl>
                <Input
                  {...field}
                  placeholder="Enter moodboard name"
                  className="bg-cr8-dark/20 border-cr8-charcoal/10"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium">Description</FormLabel>
              <FormControl>
                <Textarea
                  {...field}
                  placeholder="Enter moodboard description"
                  className="bg-cr8-dark/20 border-cr8-charcoal/10 min-h-[100px]"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          type="submit"
          className="w-full bg-purple-600 hover:bg-purple-700"
          disabled={isLoading}
        >
          {isLoading ? (
            <LoaderPinwheel className="h-4 w-4 animate-spin" />
          ) : null}
          {isLoading ? "Preparing Moodboard..." : "Start Moodboarding"}
        </Button>
      </form>
    </Form>
  );
}
