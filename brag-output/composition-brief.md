# Hyperframes Composition Brief: SilentSOS

## Objective
Create a 40-second polished security-product launch film for SilentSOS (explicit user request: professional, voiceover, transitions, 3D motion graphics, full aesthetic, 40s, cover everything).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 40 seconds (root data-duration="40")

## Source Material
- Project root: A:\pro\major\sos
- Primary files read: frontend/index.html, frontend/src/index.css, frontend/src/pages/Dashboard.tsx, frontend/src/components/ui.tsx, README.md, SOS_PLAN.md
- Product name: SilentSOS
- Tagline / strongest claim: "Possible emergency — human verification required."
- Key UI or visual moment to recreate: ops viewfinder with vf-corner brackets + ops-grid + TRACKING/POSSIBLE FALL/EMERGENCY legend + POSSIBLE EMERGENCY card (Location/Event/Confidence/Time/Camera + VERIFY/DISMISS) + confidence gauge 0–100 + temporal state chain
- Copy that must appear verbatim:
  - "Possible emergency — human verification required."
  - "Camera + Microphone → AI Detection → Temporal Verification → Emergency Confidence Engine → FastAPI → PostgreSQL + WebSocket → React Dashboard → Human Verification"
  - "Local-first. No paid AI APIs."
  - "YOLO11n-pose · ByteTrack · fall state machine"
  - "VERIFY / DISMISS"

## Creative Direction
- Tone preset: polished
- Creative direction: premium security product film — calm, trustworthy, mission-critical
- Interpretation: slow confident holds, generous letter-spacing, soft crossfades/slides, restrained SFX, steady music bed under deep male VO. 3D depth via perspective tilts, parallax grid, gauge with glow, cards landing with tilt-settle.
- Angle: The most dangerous emergencies are silent. SilentSOS watches, verifies over time, fuses vision + audio into one confidence score, and asks a human to confirm.
- Hook: flatlining pulse line + typed "The most dangerous emergency is a silent one."
- Outro / punchline: SilentSOS wordmark on paper + "Possible emergency — human verification required." + local-first line.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Emoji, gradients-for-fun, cartoon icons, AI-slop glow spam

## Visual Identity
- Background: #0E0C09 (ops near-black) for scenes 1–7; #f4f2ec paper for scene 8
- Text: #f4f2ec on dark, #16130e on light, muted #a8a08a
- Accent: #c81e1e signal + #8f1414 deep, moss #3f6212, amber #b45309, line #e2ddd0
- Display font: Space Grotesk (Google Fonts, ship local woff2 + @font-face) — fallback system sans if offline
- Body font: Inter + IBM Plex Mono for kickers/telemetry (ship local + @font-face)
- Visual references from the project: vf-corner brackets, ops-grid blueprint, ConfidenceBar, StatusBadge, dash cards, mono telemetry

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. Silence is the emergency — 4.5s — pulse line + typed hook + wordmark micro
2. The problem — 4.5s — FALL+STILLNESS / NO ONE CALLS cards + no-alert vs alert list
3. Pipeline — 5.0s — CAPTURE/DETECT/VERIFY/ALERT glass nodes + traveling beam (beat-lock ~10.93s)
4. Vision — 5.5s — viewfinder + skeleton + ID 03 TRACKING→POSSIBLE_FALL
5. Time+sound — 5.5s — 5 state cards + audio strip (final card ~22.37/22.93 cue)
6. Engine — 5.5s — 0→87 gauge + evidence rows + POSSIBLE EMERGENCY card
7. Human verifies — 5.0s — dashboard + cursor clicks VERIFY → VERIFIED
8. Outro — 4.5s — paper wordmark lockup + rule draw + hold

## Audio
- Audio role: steady professional bed under authoritative narration
- Audio arc: near-silence 0–0.6s → bed in low → steady under VO → gentle fade 37.5–40 with final bell ringing over
- Music: happy-beats-business-moves-vol-12-by-ende-dot-app.mp3
- Music treatment: volume 0.30, duck to 0.13 under voiceover 0–40s, fade-out 37.5–40. Beat/swell notes: pipeline beam ~10.93s, final state card ~22.37/22.93s, logo ~36–37s.
- Music cue guidance: preset brag/assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json — strong cues 8.74, 10.93, 13.11, 17.47, 18.56, 19.66, 22.37, 22.93, 24.56; beat grid from 0.56 spacing ~0.55s. 3 strong-cue locks max.
- Audio-reactive treatment: subtle; RMS/bass breathes ops-grid glow, bracket presence, gauge glow. No waveforms/EQ/notes/strobing as primary visual (small audio strip bars in scene 5 only, driven by timeline not live FFT, to stay deterministic).
- Audio-coupled moments:
  - Scene 1 — typing hook with key ticks + drop on headline land
  - Scene 3 — beat node reveals + beam completion bell
  - Scene 5 — card-by-card sequence + payoff bell
  - Scene 6 — counter ticks + payoff bell
  - Scene 7 — cursor click + success bell
  - Scene 8 — final logo bell
- SFX selection guidance: card arrivals = casino/card-place + interface/drop; payoff = impact/impactBell_heavy_000; UI = ui/mouseclick1 + interface/select_008; typing = keyboard/keypress randomized; success = impactBell_heavy_003 or chips-collide. Prefer low HF-risk files for repeated moments.
- SFX analysis guidance: brag/assets/sfx/sfx-analysis.md — prefer low/medium HF risk for polished repeats.
- Exact SFX choice: Hyperframes chooses filenames, timestamps, density, volume from implemented animation.
- Audio files: copy chosen music + SFX into `brag-output/composition/assets/`; VO into `assets/voiceover.wav`.

## Hyperframes Instructions
Load the composition-building Hyperframes domain skills — `hyperframes-core` (composition contract + `data-*` timing), `hyperframes-animation` (motion), `hyperframes-creative` (design spec, beats, audio-reactive), `hyperframes-keyframes` (seek-safe keyframes), and `hyperframes-cli` (lint/check/render). /brag is its own workflow: do not enter the `hyperframes` entry-point intent interview and do not route into its generic promo / launch-video workflow. Prefer native Hyperframes conventions over anything in `/brag`.

Requirements:
- Show at least one real UI, copy, or visual element from the source project.
- Keep all text readable in the final render.
- Keep the video within 40 seconds (explicit user override).
- Include the planned music/SFX/VO layer.
- Treat `/brag` audio notes as guidance, not a fixed cue sheet. Choose SFX after the visual animation exists.
- Treat music cue metadata as optional timing hints. Hyperframes decides exact animation timing and should ignore cues that hurt readability, scene pacing, or the product story.
- Major reveals may move toward nearby strong cues within about 0.15s. Smaller entrances may align to nearby beat points within about 0.10s. Use only 1-3 strong cue locks in a 40s video unless the edit clearly benefits from more.
- Use SFX to support motion and interaction: card sounds for card-like reveals, short announcement cues for major payoffs, key/click sounds for text or user actions, and restraint when the edit is already busy.
- Honor planned music treatment such as fade-outs, ducking, beat-aligned reveals, or letting a final SFX ring over the music, using the best Hyperframes-supported implementation.
- When music is present and the treatment is not `none`, consider Hyperframes audio-reactive workflow: extract audio data and use RMS/frequency bands for subtle, brand-specific motion. Good targets are glow, depth, background warmth, card presence, title emphasis, or other existing visual elements. Avoid waveform/equalizer visuals, musical-note graphics, generic particle systems, strobing, or heavy pulsing.
- Use local assets for audio and any required runtime/media dependencies when possible.
- Run `hyperframes check` before render — it is brag's single gate.
- Keep creation and rendering local. Remote or publishing workflows require a separate explicit user request.
