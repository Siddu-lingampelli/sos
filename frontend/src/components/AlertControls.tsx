import { useState } from "react";
import {
  notificationPermission,
  notificationsSupported,
  requestNotificationPermission,
  setSoundEnabled,
  soundEnabled,
  playAlertTone,
} from "../lib/notifications";

/** Operator controls for browser notifications + the audible alert tone. */
export default function AlertControls() {
  const [perm, setPerm] = useState<NotificationPermission | "unsupported">(() => notificationPermission());
  const [sound, setSound] = useState<boolean>(() => soundEnabled());

  const enableNotifications = async (): Promise<void> => {
    const next = await requestNotificationPermission();
    setPerm(next);
  };

  const toggleSound = (): void => {
    const next = !sound;
    setSound(next);
    setSoundEnabled(next);
  };

  const testAlert = (): void => {
    playAlertTone();
  };

  return (
    <span className="flex items-center gap-1.5">
      <button
        onClick={enableNotifications}
        disabled={!notificationsSupported() || perm === "granted"}
        title={
          perm === "granted"
            ? "Browser notifications enabled"
            : perm === "denied"
              ? "Notifications blocked in browser settings"
              : "Enable browser notifications"
        }
        className="rounded-md border border-[#d8d2c2] px-2 py-1 font-mono text-[11px] font-semibold text-[#57534a] hover:bg-[#faf9f5] disabled:opacity-60"
      >
        {perm === "granted" ? "NOTIFY ON" : perm === "denied" ? "NOTIFY BLOCKED" : "ENABLE NOTIFY"}
      </button>
      <button
        onClick={toggleSound}
        title="Toggle the audible alert tone"
        className="rounded-md border border-[#d8d2c2] px-2 py-1 font-mono text-[11px] font-semibold text-[#57534a] hover:bg-[#faf9f5]"
      >
        {sound ? "SOUND ON" : "SOUND OFF"}
      </button>
      <button
        onClick={testAlert}
        className="rounded-md border border-[#c81e1e] bg-[#c81e1e] px-2 py-1 font-mono text-[11px] font-bold text-white hover:bg-[#8f1414]"
        title="Test the emergency alert sound"
      >
        TEST ALERT
      </button>
    </span>
  );
}