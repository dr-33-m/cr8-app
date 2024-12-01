import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Box } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-4">
      <Box className="h-16 w-16 text-[#FFD100] mb-6" />
      <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
      <p className="text-xl text-white/70 mb-8 text-center max-w-md">
        Oops! It seems like you've ventured into uncharted territory.
      </p>
      <Button asChild className="bg-[#FFD100] text-black hover:bg-[#FFD100]/80">
        <Link to="/">Return to Dashboard</Link>
      </Button>
    </div>
  );
}
