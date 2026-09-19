# AI — SilentSOS detection pipeline (Levels 3-7)

- `vision/` — OpenCV capture + YOLO Pose + ByteTrack + fall logic (L3-L5)
- `audio/` — Silero VAD + faster-whisper keywords + distress classifier (L6)
- `engine/` — Emergency Confidence Engine fusion 0-100 (L7)

Level 1: env manifest only. Heavy model installs happen per-level to keep foundation light.
See `requirements.txt`. Create venv separately from backend if GPU/torch needed:
```powershell
python -m venv ai\venv; ai\venv\Scripts\Activate.ps1; pip install -r ai\requirements.txt
```
