"""Standalone Level 6 runner: mic or WAV -> structured distress events."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from audio_config import AudioConfig
from pipeline import AudioPipeline
from mic import MicStream, WavSource


def main():
    ap = argparse.ArgumentParser(description="SilentSOS Level 6 Audio Pipeline")
    ap.add_argument("--source", default="mic", help="'mic' or path to 16kHz mono WAV")
    ap.add_argument("--device", default=None, help="mic device id (see --list-devices)")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--duration", type=float, default=0, help="seconds to run (0 = until Ctrl+C / EOF)")
    ap.add_argument("--keywords", default="", help="comma-separated override, e.g. 'help,fire'")
    args = ap.parse_args()

    if args.list_devices:
        print(MicStream.list_devices())
        return

    cfg = AudioConfig()
    kws = tuple(k.strip() for k in args.keywords.split(",") if k.strip()) or None
    pipe = AudioPipeline(cfg, keywords=kws)

    if args.source == "mic":
        src = MicStream(cfg)
        print("[*] Opening microphone — speak / play test audio. Ctrl+C to stop.")
        src.start(device=int(args.device) if args.device else None)
    else:
        src = WavSource(args.source, cfg)
        print(f"[*] Processing {args.source}")

    t0 = time.time()
    try:
        while True:
            if args.duration and time.time() - t0 > args.duration:
                break
            blk = src.read(timeout=1.0)
            if blk is None:
                break
            for ev in pipe.process_block(blk):
                print("   ", ev)
    except KeyboardInterrupt:
        print("\n[*] Interrupted.")
    finally:
        src.stop()
        for ev in pipe.flush():
            print("   ", ev)
        print(f"[*] Done. {len(pipe.events)} events total.")


if __name__ == "__main__":
    main()
