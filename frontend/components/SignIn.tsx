import { Button } from "@/components/ui/button";
import { useLogto } from "@logto/react";
import cr8 from "@/assets/cr8.png";
import { isBrowser } from "@/lib/utils";
import { LockKeyhole } from "lucide-react";

export function SignIn() {
  // FIXME: This is a temporary solution until we have a proper way to handle authentication in the Server.
  const logto = isBrowser ? useLogto() : null;
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-4">
      <img src={cr8} alt="Cr8-xyz Logo" className="w-24 h-24 mb-4 shadow-2xl" />
      <h1 className="text-4xl font-bold mb-4">Got your keys?</h1>
      <p className="text-xl text-white/70 mb-8 text-center max-w-md">
        Open your creative space and start creating!
      </p>
      <Button
        className="bg-[#FFD100] text-black hover:bg-[#FFD100]/80 flex"
        size={"lg"}
        onClick={() => logto?.signIn(import.meta.env.VITE_SIGN_IN_URI)}
      >
        <LockKeyhole className="w-6 h-6" />
        Unlock
      </Button>
    </div>
  );
}
