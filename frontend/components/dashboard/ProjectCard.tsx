import { ChevronDown } from "lucide-react";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Link } from "@tanstack/react-router";

export function ProjectCard({ title, icon, color, items }) {
  return (
    <div
      className={`bg-white/5 backdrop-blur-md rounded-lg p-6 hover:bg-white/10 transition-colors duration-300 border border-white/10`}
    >
      <div
        className={` bg-opacity-20 rounded-full p-3 inline-block mb-4`}
        style={{ backgroundColor: `${color}20` }}
      >
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-white/70 mb-4">
        Create a stunning {title.toLowerCase()} with our easy-to-use tools.
      </p>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            className="text-white hover:bg-opacity-80"
            style={{ backgroundColor: color }}
          >
            Start Creating
            <ChevronDown className="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-40" align="center">
          {items.map((item, index) => (
            <Link to="/project" key={index}>
              <DropdownMenuItem
                key={index}
                onSelect={() => console.log(`Selected: ${item}`)}
                className="cursor-pointer"
              >
                {item}
              </DropdownMenuItem>
            </Link>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
