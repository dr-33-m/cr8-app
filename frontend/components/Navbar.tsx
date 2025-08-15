import { LogOut, Settings, User } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import cr8 from "@/assets/cr8.png";
import { Link } from "@tanstack/react-router";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useUserStore from "@/store/userStore";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { useState } from "react";
import { toast } from "sonner";
import { useLogout } from "@/lib/services/logoutService";

const Navbar = () => {
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const logout = useLogout();
  const { username } = useUserStore();

  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(import.meta.env.VITE_DISCORD_WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: `**Early Access Feedback from ${username || "Anonymous"}:**\n${feedback}`,
        }),
      });

      if (!response.ok) throw new Error("Failed to send feedback");

      toast.success("Feedback sent successfully!");
      setFeedback("");
      setIsPopoverOpen(false);
    } catch (error) {
      toast.error("Failed to send feedback. Please try again.");
      console.error("Error sending feedback:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isVisible = useVisibilityStore((state) => !state.isFullscreen);

  const handleSignOut = async () => {
    await logout();
  };

  return username ? (
    <nav
      className={`fixed top-4 left-4 right-4 z-50 transition-all transform -translate-y-1/2 duration-300  ${isVisible ? "translate-y-0" : "-translate-y-full"} `}
    >
      <div className="container mx-auto">
        <div className="bg-cr8-charcoal/10 backdrop-blur-md rounded-lg border border-white/10 shadow-lg">
          <div className="flex justify-between items-center px-6 py-3">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <img src={cr8} alt="Cr8-xyz" className="w-10 h-10 shadow-lg" />
                <span className="ml-2 text-xl font-semibold">Cr8-xyz</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
                <PopoverTrigger>
                  <Badge className="ml-2">Early Access</Badge>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="space-y-4">
                    <h4 className="font-medium leading-none">Send Feedback</h4>
                    <p className="text-sm text-muted-foreground">
                      Your feedback helps us make Cr8-xyz better for you
                    </p>
                    <Textarea
                      placeholder="Type your feedback here..."
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      className="min-h-[100px]"
                    />
                    <Button
                      onClick={handleSubmitFeedback}
                      disabled={isSubmitting || !feedback.trim()}
                      className="w-full"
                    >
                      {isSubmitting ? "Sending..." : "Submit Feedback"}
                    </Button>
                  </div>
                </PopoverContent>
              </Popover>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-8 w-8 rounded-full"
                  >
                    <User className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {username}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {false && (
                    <DropdownMenuItem className="text-white hover:bg-white/10">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    className="text-white hover:bg-white/10"
                    onClick={handleSignOut}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>
    </nav>
  ) : null;
};

export default Navbar;
