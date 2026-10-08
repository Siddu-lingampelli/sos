# Brag Plan: SilentSOS

## What is this app?
SilentSOS is a local-first AI emergency detection system for hostels and campuses — camera + microphone → YOLO pose + tracking + fall temporal verification + distress audio → confidence engine → real-time security dashboard for human verification.

## The angle
A calm, mission-critical product film. No hype, no jokes. The premise: the most dangerous emergencies are silent — a fall with no one to call for help. SilentSOS watches, verifies over time, and asks a human to confirm. Play it like a Bosch / Honeywell security launch: dark ops-room, viewfinder brackets, confidence gauge, VERIFY button. Every claim on screen is quoted from the repo.

## Hook (first 2-3 seconds)
Black. A thin ECG-style line goes flat. Line of mono text types: "The most dangerous emergency is a silent one." Then SilentSOS wordmark slams in with signal-red underline. This earns the next 37 seconds.

## Key moments (the middle)
- The live viewfinder: dark ops panel, corner brackets, skeleton tracking dots, TRACKING / POSSIBLE FALL / EMERGENCY legend — recreated from Dashboard.tsx + index.css.
- The temporal truth: NORMAL → POSSIBLE_FALL → OBSERVING → INACTIVE → POSSIBLE_EMERGENCY state chain animating, "verifies over an observation window" (never a single frame).
- The confidence engine: 0–100 gauge counting to 87, fusing Fall + Inactivity + Distress keyword "help" — then the POSSIBLE EMERGENCY card with Location / Event / Confidence / Time / Camera + VERIFY / DISMISS.

## Outro / punchline
SilentSOS wordmark on paper background. "Possible emergency — human verification required." + "Local-first. No paid AI APIs." Hold. Quiet logo hit. End.

## User flow worth showing
Entry → key action → result, from the real app:
- Start camera (laptop / mobile / manual-IP picker) → engine ARMED, feed LIVE
- Person falls, stays motionless, says "help" → confidence climbs, WebSocket pushes instantly
- Operator opens incident, presses VERIFY, incident preserved in history

## Tone
- Preset: polished
- Creative direction: premium security product film — calm, trustworthy, mission-critical
- Interpretation: Fewer scenes with longer holds (5s each), generous letter-spacing, soft crossfades and slides, restrained SFX, music as a steady bed under a deep male voiceover. Confidence through restraint, scale through 3D depth (tilted ops panels, parallax grid, gauge with real perspective).

## Format: landscape — 1920x1080
## Duration: 40 seconds (explicit user request; overrides 15–25s default)

## Visual identity (from the project)
- Background: #0E0C09 (ops-room near-black, derived from --color-ink #16130e deepened for video) with paper #f4f2ec for outro
- Accent: #c81e1e (signal) + deep #8f1414, support moss #3f6212, amber #b45309
- Text: #f4f2ec on dark, #16130e on light, muted #a8a08a / #57534a
- Display font: Space Grotesk (700/600, tight tracking, uppercase kickers in IBM Plex Mono)
- Body font: Inter (400/500) + IBM Plex Mono for all telemetry/kickers
- Strongest visual element: live-feed viewfinder with vf-corner brackets + ops-grid blueprint + confidence bar + POSSIBLE EMERGENCY alert card

## Share copy (draft)
Introducing SilentSOS: local AI that watches for falls, stillness and distress calls, verifies over time, and asks a human to confirm. Possible emergency — human verification required.

## Audio direction
- Role: steady professional bed under authoritative narration
- Music: happy-beats-business-moves-vol-12-by-ende-dot-app.mp3 (steady and clean, 109.96 BPM) — best for polished
- Music treatment: start at 0.0, volume 0.30, duck to 0.13 under voiceover (0–40s), fade out 37.5–40s. Beat/swell notes: lock Scene 3 pipeline reveal near 8.74s, Scene 5 engine near 24.5s region, final logo near 36–37s.
- Music cue guidance: preset read (vol-12 cues). Strong cues in window: 8.74s, 10.93s, 13.11s, 17.47s, 18.56s, 19.66s, 22.37s, 22.93s, 24.56s. Beat grid ~0.55s spacing from 0.56s. Use 3 strong-cue locks max (pipeline reveal, confidence payoff, logo); snap sequential cards to every-other beat for readability.
- Audio-reactive treatment: subtle; music RMS/bass breathes the ops-grid glow, viewfinder bracket presence, and confidence gauge glow. No waveforms, no equalizer bars, no notes, no strobing.
- SFX posture: sparse, motion-matched, professional restraint — soft drops for card arrivals, one deep bell for POSSIBLE EMERGENCY, UI clicks for VERIFY, card slides for state chain.
- Audio-coupled moments: typed hook line with key ticks; count-up gauge with soft ticks; state chain cards arriving one by one; VERIFY cursor click; final logo bell.
- Restraint rule: music and SFX must never fight the voiceover. No glitch, no punch, no chaos. Silence under the hook's first 0.6s, then bed fades in.

## Voiceover script
Professional, calm, deep male delivery (Kokoro am_michael). ~100 words for 40s. Complements visuals, never reads on-screen text verbatim.

> "The most dangerous emergency… is a silent one. A fall. No call for help. Nobody watching. SilentSOS watches — camera and microphone, verified over time. Pose, tracking, stillness, and distress — fused into one confidence score. And when it matters, it asks a human to confirm. SilentSOS. Possible emergency — human verification required."

WAV: composition/assets/voiceover.wav. Music ducks to 0.12–0.15 for its duration.

## Storyboard

### Scene 1 — Silence is the emergency — 4.5s (0.0–4.5)
Black ops-room. Thin signal-red pulse line draws across frame, settles. Mono kicker types: "HOSTEL / CAMPUS — 02:14 AM". Headline holds: "The most dangerous emergency is a silent one." SilentSOS micro-wordmark fades in corner. 3D: pulse line has glow + slight camera push-in (scale 1.04→1.0).
Sequential/interaction: kicker types char by char; headline words fade up one by one; then hold.
Audio intent: near-silence 0–0.6s, then music bed fades in low; soft key ticks under typing.
Audio-coupled idea: typing with randomized keyboard ticks; one soft drop when headline lands.
Music: vol-12 bed, fade in from 0.6s
Transition mood: soft crossfade → Scene 2

### Scene 2 — The problem it solves — 4.5s (4.5–9.0)
Paper-textured dark card split: left "FALL + NO MOVEMENT", right "NO ONE CALLS FOR HELP". Small mono list from the spec: Walking → no alert / Sitting → no alert / Fall + stillness → alert. Red rule wipes between.
Sequential/interaction: two cards slide in one by one (left, right); three list rows arrive staggered.
Audio intent: bed steady; two soft drops on card arrivals.
Audio-coupled idea: card-by-card sequence with card-place sounds.
Music: bed continues
Transition mood: clean slide → Scene 3

### Scene 3 — The pipeline — 5.0s (9.0–14.0)
"Camera + Microphone → AI → Verify → Alert" horizontal pipeline with 4 glass nodes + connecting beam pulse traveling left→right. Node labels: CAPTURE / DETECT / VERIFY / ALERT. Beat-locked reveal near 8.74–9.3 cue window (pipeline beam fires). 3D: nodes tilt in perspective (rotationX/rotationY), beam has glow, subtle parallax on grid.
Sequential/interaction: 4 nodes arrive on every-other beat; beam pulse travels after 4th lands.
Audio intent: rising confidence; soft ticks per node, one warm bell when beam completes.
Audio-coupled idea: beat-aligned node reveal + traveling pulse.
Music: bed steady (strong cue ~10.93s for beam fire)
Transition mood: dramatic wipe with scale → Scene 4

### Scene 4 — Vision: pose + tracking + fall — 5.5s (14.0–19.5)
Recreated ops viewfinder: dark panel, vf-corner brackets, silhouette figure with skeleton joints + ID tag "ID 03 · TRACKING", legend row TRACKING / POSSIBLE FALL / EMERGENCY. Status flips TRACKING → POSSIBLE_FALL with amber flash. Caption: "YOLO11n-pose · ByteTrack · fall state machine".
Sequential/interaction: brackets draw in, figure + skeleton fades up, ID tag pops, status flips once.
Audio intent: technical, precise; soft UI click on status flip.
Audio-coupled idea: simulated tracking lock (select click) + status flip.
Music: bed continues
Transition mood: clean push → Scene 5

### Scene 5 — Time + sound verify it — 5.5s (19.5–25.0)
State chain NORMAL → POSSIBLE_FALL → OBSERVING → INACTIVE → POSSIBLE_EMERGENCY, cards arriving left→right, final card glows red. Below: audio strip "VAD · faster-whisper · 'help' · scream" with waveform bars reacting subtly. Caption: "Observation window. Never a single frame."
Sequential/interaction: 5 state cards arrive one by one on beat grid; waveform draws; final card gets red glow + bell.
Audio intent: tension builds; card-place per card, deep bell on final.
Audio-coupled idea: card-by-card sequence + waveform draw + payoff bell.
Music: bed steady (strong cues 22.37/22.93 for final card)
Transition mood: soft crossfade → Scene 6

### Scene 6 — Confidence engine — 5.5s (25.0–30.5)
Big 0–100 gauge counting 0→87 with 3D tilt + glow. Evidence rows stack: FALL strong / INACTIVITY supporting / DISTRESS "help" supporting / RECOVERY clears. POSSIBLE EMERGENCY card slams: Location B-Block / FALL+STILLNESS / 87% / 02:14 / CAM 01. 3D: gauge ring rotates slightly, card lands with perspective tilt settling flat.
Sequential/interaction: evidence rows stack one by one; gauge counts; alert card lands last.
Audio intent: payoff; counter ticks under count-up, one deep announcement bell on card land.
Audio-coupled idea: counter ticks + beat-locked payoff reveal.
Music: bed steady, slight lift
Transition mood: dramatic crossfade with scale → Scene 7

### Scene 7 — Human verifies — 5.0s (30.5–35.5)
Recreated dashboard: left live feed mini, right alert queue (#1041 OPEN 87%), bottom logs tail, VERIFY / DISMISS buttons. Cursor glides and clicks VERIFY → badge flips OPEN → VERIFIED (moss green), log row appends "VERIFIED by operator". Caption: "WebSocket. No refresh. Human decides."
Sequential/interaction: simulated cursor click on VERIFY; badge flips; log row slides in.
Audio intent: resolution; mouse click + soft success bell on flip.
Audio-coupled idea: simulated tap/click + success accent.
Music: bed steady, starts gentle fade at 35s
Transition mood: soft crossfade to paper → Scene 8

### Scene 8 — Outro / wordmark — 4.5s (35.5–40.0)
Paper #f4f2ec background. SilentSOS wordmark (Space Grotesk 700) centers, signal-red rule draws under. Lines hold: "Possible emergency — human verification required." + mono sub "LOCAL-FIRST · NO PAID AI APIs · FASTAPI + REACT + POSTGRES". Music fades 37.5–40, final logo bell rings over the fade, then silence.
Sequential/interaction: none — one confident lockup, rule draws, then hold.
Audio intent: landing; final bell, bed out, voice tag closes.
Audio-coupled idea: final logo payoff.
Music: fade out 37.5–40.0
Transition mood: end hold (no exit)

**Music mood for this video:** steady, clean, professional corporate bed (vol-12)
**Audio summary:** Near-silence into a steady low bed that ducks under a calm deep male voiceover, with sparse motion-matched drops/clicks, a deep bell on each payoff, and a quiet logo ring over the final fade.
