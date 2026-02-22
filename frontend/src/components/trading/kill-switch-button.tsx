"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ShieldAlert, Loader2 } from "lucide-react";
import { useKillSwitch } from "@/hooks/use-api";

export function KillSwitchButton() {
  const killSwitch = useKillSwitch();
  const [confirming, setConfirming] = useState(false);

  // Auto-reset confirmation after 5 seconds
  useEffect(() => {
    if (!confirming) return;
    const timer = setTimeout(() => setConfirming(false), 5_000);
    return () => clearTimeout(timer);
  }, [confirming]);

  function handleClick() {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    killSwitch.mutate(undefined, {
      onSettled: () => setConfirming(false),
    });
  }

  return (
    <div className="space-y-1">
      <Button
        variant="destructive"
        onClick={handleClick}
        disabled={killSwitch.isPending}
        className="w-full"
      >
        {killSwitch.isPending ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <ShieldAlert className="mr-2 h-4 w-4" />
        )}
        {confirming ? "CONFIRM KILL SWITCH" : "Kill Switch"}
      </Button>
      {killSwitch.data && (
        <p className="text-xs text-muted-foreground">
          Cancelled {killSwitch.data.cancelled_orders} orders, closed{" "}
          {killSwitch.data.closed_positions} positions
        </p>
      )}
      {killSwitch.error && (
        <p className="text-xs text-destructive">
          {String(killSwitch.error)}
        </p>
      )}
    </div>
  );
}
