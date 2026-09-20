import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { DEFAULT_CAMERA_SOURCE } from "./api";

export type CamMode = "laptop" | "mobile" | "manual";

interface CameraState {
  mode: CamMode;
  setMode: (m: CamMode) => void;
  mobileUrl: string;
  setMobileUrl: (u: string) => void;
  manualUrl: string;
  setManualUrl: (u: string) => void;
  activeSource: string;
}

const CameraCtx = createContext<CameraState | null>(null);

function load(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function save(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode — ignore */
  }
}

export function CameraProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<CamMode>(() =>
    DEFAULT_CAMERA_SOURCE === "0" ? "laptop" : "mobile",
  );
  const [mobileUrl, setMobileUrlRaw] = useState<string>(() =>
    load(
      "sos.cam.mobile",
      DEFAULT_CAMERA_SOURCE && DEFAULT_CAMERA_SOURCE !== "0"
        ? DEFAULT_CAMERA_SOURCE
        : "http://192.168.1.33:8080/video",
    ),
  );
  const [manualUrl, setManualUrlRaw] = useState<string>(() => load("sos.cam.manual", ""));

  const setMobileUrl = useCallback((u: string) => {
    setMobileUrlRaw(u);
    save("sos.cam.mobile", u);
  }, []);
  const setManualUrl = useCallback((u: string) => {
    setManualUrlRaw(u);
    save("sos.cam.manual", u);
  }, []);

  const activeSource = mode === "laptop" ? "0" : mode === "mobile" ? mobileUrl : manualUrl;

  const value = useMemo(
    () => ({ mode, setMode, mobileUrl, setMobileUrl, manualUrl, setManualUrl, activeSource }),
    [mode, mobileUrl, setMobileUrl, manualUrl, setManualUrl, activeSource],
  );
  return <CameraCtx.Provider value={value}>{children}</CameraCtx.Provider>;
}

export function useCamera(): CameraState {
  const ctx = useContext(CameraCtx);
  if (!ctx) throw new Error("useCamera must be used inside CameraProvider");
  return ctx;
}
