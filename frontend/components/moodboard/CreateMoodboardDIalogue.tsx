import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

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
        <div className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="name" className="text-sm font-medium">
              Moodboard Name
            </Label>
            <Input
              id="name"
              placeholder="Enter moodboard name"
              className="bg-cr8-dark/20 border-cr8-charcoal/10"
            />
          </div>
          <div className="space-y-3">
            <Label htmlFor="description" className="text-sm font-medium">
              Description
            </Label>
            <Textarea
              id="description"
              placeholder="Enter moodboard description"
              className="bg-cr8-dark/20 border-cr8-charcoal/10 min-h-[100px]"
            />
          </div>
          <Button className="w-full bg-purple-600 hover:bg-purple-700">
            Start Moodboarding
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
