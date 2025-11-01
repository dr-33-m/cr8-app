import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import cr8 from "@/assets/cr8.png";

export function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-linear-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-4">
      <img src={cr8} alt="Cr8-xyz Logo" className="w-24 h-24 mb-4 shadow-2xl" />
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
