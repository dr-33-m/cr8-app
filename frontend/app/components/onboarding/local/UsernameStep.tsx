import { Input } from "@/components/ui/input";
import { UsernameStepProps } from "@/lib/types/onboarding";

export function UsernameStep({
  username,
  onUsernameChange,
  onEnterPress,
}: UsernameStepProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onEnterPress();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-semibold mb-2 text-foreground">
          Enter Username
        </h3>
        <p className="text-muted-foreground text-sm">
          Choose a username for your session
        </p>
      </div>
      <Input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => onUsernameChange(e.target.value)}
        onKeyPress={handleKeyPress}
      />
    </div>
  );
}
