import { Tablet, Monitor } from "lucide-react";
import cr8 from "@/assets/cr8.png";

export function MobileMessage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white p-6 text-center">
      <img src={cr8} alt="Cr8-xyz Logo" className="w-20 h-20 mb-6" />
      <h1 className="text-2xl font-semibold mb-6">We currently support:</h1>
      <div className="space-y-4">
        <div className="flex items-center justify-center space-x-2">
          <Tablet className="w-6 h-6" />
          <span className="text-lg">Tablets</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Monitor className="w-6 h-6" />
          <span className="text-lg">PC</span>
        </div>
      </div>

      {/* Message */}
      <p className="text-white/70 mt-6 text-sm max-w-xs">
        Please switch to a supported device to continue.
      </p>
    </div>
  );
}
