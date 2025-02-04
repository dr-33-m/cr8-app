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
import { useLogto } from "@logto/react";
import { isBrowser } from "@/lib/utils";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useUserStore from "@/store/userStore";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Badge } from "./ui/badge";

const Navbar = () => {
  const logto = isBrowser ? useLogto() : null;
  const isVisible = useVisibilityStore((state) => !state.isFullscreen);
  const { userInfo, resetUserInfo } = useUserStore((store) => store);

  const handleSignOut = async () => {
    if (logto) {
      await logto.signOut(import.meta.env.VITE_SIGN_OUT_URI);
      resetUserInfo();
    }
  };
  return logto?.isAuthenticated ? (
    <nav
      className={`fixed top-4 left-4 right-4 z-50 transition-all transform -translate-y-1/2 duration-300  ${isVisible ? "translate-y-0" : "-translate-y-full"} `}
    >
      <div className="container mx-auto">
        <div className="bg-white/10 backdrop-blur-md rounded-lg border border-white/20 shadow-lg">
          <div className="flex justify-between items-center px-6 py-3">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <img src={cr8} alt="Cr8-xyz" className="w-10 h-10 shadow-lg" />
                <span className="ml-2 text-xl font-semibold">Cr8-xyz</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Badge className="ml-2">Early Access</Badge>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-sm">
                      Your feedback helps us make Cr8-xyz better for you
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
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
                        {userInfo?.username || "John Doe"}
                      </p>
                      <p className="text-xs leading-none text-white/70">
                        {userInfo?.email || "yourEmailHere"}
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
