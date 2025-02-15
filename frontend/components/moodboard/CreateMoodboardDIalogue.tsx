import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { MoodboardForm } from "./MoodboardForm";

export function CreateMoodboardDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          size="lg"
          className="bg-cr8-purple hover:bg-cr8-purple/20 text-white w-full"
        >
          Create Moodboard
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] bg-cr8-charcoal/95 backdrop-blur-xl border-white/10">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Create New Moodboard
          </DialogTitle>
        </DialogHeader>
        <MoodboardForm />
      </DialogContent>
    </Dialog>
  );
}
