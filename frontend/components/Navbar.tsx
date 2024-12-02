import { LogOut, Search, Settings, User } from "lucide-react";
import { Input } from "./ui/input";
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

const Navbar = () => {
  // FIXME: This is a temporary solution until we have a proper way to handle authentication in the Server.
  const logto = isBrowser ? useLogto() : null;

  return logto?.isAuthenticated ? (
    <nav className="fixed top-4 left-4 right-4 z-50">
      <div className="container mx-auto">
        <div className="bg-white/10 backdrop-blur-md rounded-lg border border-white/20 shadow-lg">
          <div className="flex justify-between items-center px-6 py-3">
            <div className="flex items-center">
              <Link href="/" className="flex items-center">
                <img src={cr8} alt="Cr8-xyz" className="w-10 h-10 shadow-lg" />
                <span className="ml-2 text-xl font-semibold">Cr8-xyz</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Input
                type="text"
                placeholder="Search..."
                className="bg-white/10 border-white/20 text-white placeholder-white/50 w-64"
              />
              <Button variant="ghost" size="icon" className="rounded-full">
                <Search className="h-5 w-5" />
                <span className="sr-only">Search</span>
              </Button>
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
                        john Doe
                      </p>
                      <p className="text-xs leading-none text-white/70">
                        john@example.com
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-white hover:bg-white/10">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-white hover:bg-white/10"
                    onClick={() =>
                      logto?.signOut(import.meta.env.VITE_SIGN_OUT_URI)
                    }
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
