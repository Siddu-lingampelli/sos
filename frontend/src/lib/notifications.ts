/** Level 9 operator alerts: browser notification + audible tone.

 *  Everything is best-effort and gated on the operator's own permission and
 *  preference, so a denied permission or missing audio context never blocks
 *  the dashboard from showing the visual alert.
 */

const SOUND_KEY = "sos.alert.sound";

export function soundEnabled(): boolean {
  try {
    return localStorage.getItem(SOUND_KEY) !== "off";
  } catch {
    return true;
  }
}

export function setSoundEnabled(on: boolean): void {
  try {
    localStorage.setItem(SOUND_KEY, on ? "on" : "off");
  } catch {
    /* private mode */
  }
}

export function notificationsSupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

export function notificationPermission(): NotificationPermission | "unsupported" {
  return notificationsSupported() ? Notification.permission : "unsupported";
}

export async function requestNotificationPermission(): Promise<NotificationPermission | "unsupported"> {
  if (!notificationsSupported()) return "unsupported";
  try {
    return await Notification.requestPermission();
  } catch {
    return "denied";
  }
}

export function notifyIncident(eventType: string, confidence: number, body?: string, id?: number): void {
  if (!notificationsSupported() || Notification.permission !== "granted") return;
  // One tag per incident: a shared tag used to let each new firing silently
  // replace (bury) the previous sticky alert. Tabs also coordinate through
  // localStorage so two open tabs don't stack duplicate banners.
  const key = "sos.alert.seen";
  try {
    const raw = localStorage.getItem(key);
    if (raw && id !== undefined) {
      const seen = JSON.parse(raw) as { id: number; at: number };
      if (seen.id === id && Date.now() - seen.at < 30000) return;
    }
    if (id !== undefined) {
      localStorage.setItem(key, JSON.stringify({ id, at: Date.now() }));
    }
  } catch {
    /* private mode — notify anyway */
  }
  try {
    new Notification("SilentSOS — possible emergency", {
      body: `${eventType} · ${Math.round(confidence * 100)}%${body ? ` · ${body}` : ""}`,
      tag: id !== undefined ? `silentsos-${id}` : "silentsos-emergency",
      requireInteraction: true,
    });
  } catch {
    /* notification constructor can throw on some platforms */
  }
}

let audioCtx: AudioContext | null = null;
let lastToneAt = 0;
const TONE_MIN_GAP_MS = 2000;

/** Two descending pulses — distinct from any OS notification sound. */
export function playAlertTone(): void {
  if (!soundEnabled()) return;
  // A burst of firings must not stack overlapping oscillators.
  const nowMs = Date.now();
  if (nowMs - lastToneAt < TONE_MIN_GAP_MS) return;
  lastToneAt = nowMs;
  try {
    const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return;
    audioCtx = audioCtx ?? new Ctor();
    if (audioCtx.state === "suspended") void audioCtx.resume();
    const now = audioCtx.currentTime;
    [880, 620].forEach((freq, i) => {
      const osc = audioCtx!.createOscillator();
      const gain = audioCtx!.createGain();
      osc.type = "square";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, now + i * 0.22);
      gain.gain.exponentialRampToValueAtTime(0.12, now + i * 0.22 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.22 + 0.2);
      osc.connect(gain).connect(audioCtx!.destination);
      osc.start(now + i * 0.22);
      osc.stop(now + i * 0.22 + 0.22);
    });
  } catch {
    /* audio unavailable */
  }
}