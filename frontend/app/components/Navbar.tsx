import { LogOut, Settings, User, Moon, Sun, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
} from "@/components/ui/dropdown-menu";
import cr8 from "@/assets/cr8.jpeg";
import { Link } from "@tanstack/react-router";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";
import { toast } from "sonner";
import { signOutFn } from "@/server/auth/functions";
import { useTheme } from "next-themes";
import type { AuthContext } from "@/lib/types/auth";
import useUserStore from "@/store/userStore";
import { useLogout } from "@/lib/services/logoutService";

const isRemoteMode = import.meta.env.VITE_LAUNCH_MODE === "remote";

interface NavbarProps {
  auth: AuthContext;
}

const Navbar = ({ auth }: NavbarProps) => {
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const { setTheme } = useTheme();
  const localUsername = useUserStore((s) => s.username);
  const localLogout = useLogout();

  // Remote mode: username from auth context; Local mode: username from store
  const username = isRemoteMode
    ? (auth.isAuthenticated ? auth.user.name : null)
    : (localUsername || null);

  // In local mode, show navbar when username is set; in remote mode, when authenticated
  const showNavbar = isRemoteMode ? auth.isAuthenticated : !!localUsername;

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
    if (isRemoteMode) {
      // Clear local stores, then redirect to Logto sign-out
      window.dispatchEvent(new CustomEvent("logout-disconnect"));
      const { redirectUrl } = await signOutFn();
      window.location.href = redirectUrl;
    } else {
      // Local mode: clear stores and navigate home
      await localLogout();
    }
  };

  return showNavbar ? (
    <nav
      className={`fixed top-4 left-4 right-4 z-50 transition-all transform -translate-y-1/2 duration-300  ${isVisible ? "translate-y-0" : "-translate-y-full"} `}
    >
      <div className="container mx-auto">
        <div className="bg-card border rounded-lg shadow-lg">
          <div className="flex justify-between items-center px-6 py-3">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <img
                  src={cr8}
                  alt="Cr8-xyz"
                  className="w-10 h-10 shadow-xs rounded-md"
                />
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
                <DropdownMenuTrigger>
                  <Button variant="ghost" className="relative h-8 w-8">
                    <User className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {username}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuSub>
                    <DropdownMenuSubTrigger className="text-foreground hover:bg-accent">
                      <Palette className="mr-2 h-4 w-4" />
                      <span>Theme</span>
                    </DropdownMenuSubTrigger>
                    <DropdownMenuPortal>
                      <DropdownMenuSubContent className="w-48" sideOffset={-4}>
                        <DropdownMenuItem
                          className="text-foreground hover:bg-accent"
                          onClick={() => setTheme("light")}
                        >
                          <Sun className="mr-2 h-4 w-4" />
                          <span>Light</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-foreground hover:bg-accent"
                          onClick={() => setTheme("dark")}
                        >
                          <Moon className="mr-2 h-4 w-4" />
                          <span>Dark</span>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-foreground hover:bg-accent"
                          onClick={() => setTheme("system")}
                        >
                          <Settings className="mr-2 h-4 w-4" />
                          <span>System</span>
                        </DropdownMenuItem>
                      </DropdownMenuSubContent>
                    </DropdownMenuPortal>
                  </DropdownMenuSub>
                  <DropdownMenuSeparator />
                  {false && (
                    <DropdownMenuItem className="text-foreground hover:bg-accent">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    className="text-foreground hover:bg-accent"
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
