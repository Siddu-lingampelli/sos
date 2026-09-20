# AI — SilentSOS detection pipeline

- `vision/` — OpenCV capture + YOLO Pose + ByteTrack + fall logic + inactivity (L3-L5 ✅)
- `audio/` — mic/WAV → Silero VAD → faster-whisper keywords + distress classifier (L6 ✅)
- `engine/` — Emergency Confidence Engine fusion 0-100 (**Level 7 — not built yet**)

## Audio quickstart (Level 6)

```powershell
python -m venv ai\venv; ai\venv\Scripts\Activate.ps1; pip install -r ai\requirements.txt
cd ai\audio
python run_audio.py --list-devices            # find your mic id
python run_audio.py --source mic              # live: speak / play test sounds
python run_audio.py --source test.wav         # file: 16kHz mono WAV
python run_audio.py --source mic --keywords "help,fire"   # custom keywords
```

First run downloads Silero VAD (~2MB, torch.hub) and whisper-tiny (~75MB) once.
Events printed: `SPEECH_DETECTED`, `DISTRESS_KEYWORD`, `DISTRESS_SOUND`.
