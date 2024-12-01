import { Button } from "@/components/ui/button";
import { Box } from "lucide-react";
import { useLogto } from "@logto/react";

export function SignIn() {
  //   const { signIn } = useLogto();
  const logto = typeof window !== "undefined" ? useLogto() : null;
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-4">
      <Box className="h-16 w-16 text-[#FFD100] mb-6" />
      <h1 className="text-4xl font-bold mb-4">You havent Signed In</h1>
      <p className="text-xl text-white/70 mb-8 text-center max-w-md">
        Please Sign In first before accessing the dashboard.
      </p>
      <Button
        className="bg-[#FFD100] text-black hover:bg-[#FFD100]/80"
        size={"lg"}
        onClick={() => logto?.signIn("http://localhost:3000/callback")}
      >
        Sign In
      </Button>
    </div>
  );
}
