# Drone Detection & Tracking Turret 🎯

A low-cost system that **hears a drone** with a microphone array, **swings a camera toward it**, and then **locks on visually** with a pan-tilt turret, using sound first and sight second.

> **Status:** 🟡 In progress, Part A (acoustic detector)

<!-- Replace with your best photo, render, or GIF once you have one -->
<!-- ![Project image](media/hero.jpg) -->

---

## 🎯 Goal
Detect a small drone by its propeller sound, estimate which direction it's coming from, hand that bearing to a camera turret, and keep the drone centered in frame, then measure detection range, bearing accuracy, and tracking error.

## ⚙️ How it works
1. **Hear:** a 4-mic array on a Raspberry Pi listens for the drone's propeller buzz (energy in the few-hundred-Hz to few-kHz band, compared with background noise).
2. **Locate:** the SRP-PHAT algorithm compares tiny arrival-time differences between the mics to estimate the drone's bearing.
3. **Point:** the bearing commands the pan servo to swing the camera toward the sound.
4. **Lock on:** OpenCV finds the target in the camera frame, and a control loop keeps it centered.

## 🗺️ Roadmap
- [ ] **Part A: Acoustic detector:** detection + direction finding; calibrate bearing error at 30° increments
- [ ] **Part B: Tracking turret:** pan-tilt camera mount, OpenCV target tracking, controller tuning
- [ ] **Part C: Combined system:** acoustic cue hands off to the camera, which takes over tracking
- [ ] **Testing & write-up:** detection range, bearing accuracy, tracking error, response time

## 📈 Progress log
| Date | Milestone | Notes |
|------|-----------|-------|
| 11/04/2026 | Project started | Defined scope and roadmap |
| 11/04/2026 | Built laptop acoustic detection script | Flags drone buzz by sound energy in the 200–2500 Hz band vs. background; validated on synthetic drone audio |
| 11/04/2026 | First test on a 48 s drone recording | Detection flickered on and off; diagnosed the cause and fixed it (see below) |
| 11/04/2026 | Re-tested with fix | One continuous detection from ~3.6 s to ~44.7 s, held through a dip at ~32 s |
| | | |

## 📊 Results
**Acoustic detection on a 48 s drone recording** ([code](acoustic/drone_detect_laptop.py)): one continuous detection while the drone is present. Top: spectrogram, where the drone's harmonics show as stacked horizontal lines. Bottom: energy in the drone band vs. the ON/OFF thresholds.

![Detection after fix](media/After_Fix.png)

*Coming soon:* bearing error vs. true angle, detection range, and tracking error over time.

## 🧰 Tech stack
- **Software:** Python, NumPy, SciPy, sounddevice, pyroomacoustics (SRP-PHAT), OpenCV
- **Hardware:** Raspberry Pi, 4-mic array board, Pi camera, pan-tilt servo mount
- **CAD:** SolidWorks / Fusion 360

## 📁 Repository structure
```
drone-tracking-turret/
├── acoustic/     # detection & direction finding (drone_doa.py)
├── turret/       # camera tracking & servo control
├── combined/     # acoustic-to-camera handoff
├── hardware/     # CAD files, wiring diagrams
├── data/         # recordings & test logs
├── media/        # photos, videos, plots
└── README.md
```

## 🧠 What I'm learning
<!-- Update as you go: problems you hit and how you solved them. Recruiters read this. -->
- **Background estimation (11/04):** On my first test with a 48-second drone recording, the detector flickered on and off even though the drone was audible the whole time. The cause: the script estimated background noise from the quietest 20% of the clip, but the drone was present for ~80% of it, so the "background" already included drone sound. That pushed the threshold up to the drone's own level, and every small wobble crossed it.
  - **Fix 1:** learn the background from the first 3 seconds (drone-free), the same calibration step the Raspberry Pi version will use.
  - **Fix 2:** hysteresis, meaning separate ON (+6 dB) and OFF (+3 dB) thresholds, so small level changes near the line don't toggle the detection.
  - **Result:** background dropped from ~46 dB to ~35.5 dB, and the detector now gives one continuous detection for the whole time the drone is present, even through a ~6 dB dip.

  | Before (flickering) | After (fixed) |
  |---|---|
  | ![Before fix](media/Before_Fix.png) | ![After fix](media/After_Fix.png) |

  - **Takeaway:** a detector is only as good as its noise reference. Next: test decoys (fans, traffic, lawnmowers) to see what fools a pure loudness check.

## ⚠️ Scope
This is a passive detection and tracking system only. It carries no effector and does not interfere with any aircraft. Testing uses recorded drone audio and indoor sub-250 g drones; any outdoor flights follow FAA recreational rules outside restricted airspace.

---
*Built by Mat Yohannes · Mechanical Engineering, Howard University*
