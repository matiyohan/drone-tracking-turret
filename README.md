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
| | | |

## 📊 Results
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
- 

## ⚠️ Scope
This is a passive detection and tracking system only. It carries no effector and does not interfere with any aircraft. Testing uses recorded drone audio and indoor sub-250 g drones; any outdoor flights follow FAA recreational rules outside restricted airspace.

---
*Built by Mat Yohannes · Mechanical Engineering, Howard University*
