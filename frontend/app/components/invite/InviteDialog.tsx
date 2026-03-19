import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { redeemInviteFn } from "@/server/api/invitations/functions";

interface InviteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accessToken: string;
  onSuccess: () => void;
}

export function InviteDialog({
  open,
  onOpenChange,
  accessToken,
  onSuccess,
}: InviteDialogProps) {
  const [token, setToken] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await redeemInviteFn({
        data: { token: token.trim(), accessToken },
      });
      toast.success("Invite accepted! You can now launch projects.");
      onSuccess();
      onOpenChange(false);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to redeem invite";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Early Access</DialogTitle>
          <DialogDescription>
            Cr8 is currently in private beta. Enter your invite token below to
            unlock project launching. If you don't have one, reach out to{" "}
            <span className="font-medium text-foreground">
              hello@cr8-xyz.art
            </span>{" "}
            to request access.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label
              htmlFor="invite-token"
              className="text-sm font-medium leading-none"
            >
              Invite Token
            </label>
            <Input
              id="invite-token"
              placeholder="Paste your invite token..."
              value={token}
              onChange={(e) => {
                setToken(e.target.value);
                setError("");
              }}
              disabled={isSubmitting}
              autoFocus
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !token.trim()}>
              {isSubmitting ? "Verifying..." : "Redeem Invite"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
