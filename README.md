# Drone Detection & Tracking Turret 🎯

A camera-based system that **detects small drones** using computer vision and **tracks them in real time** on a pan-tilt turret with closed-loop control.

> **Status:** 🟡 In progress, Phase 1 (detection)

<!-- Replace with your best photo, render, or GIF once you have one -->
<!-- ![Project image](media/hero.jpg) -->

---

## 🎯 Goal
Build a low-cost sensing system that can spot a small drone in a camera feed, distinguish it from birds and background clutter, and keep it centered in frame as it moves, then measure how accurately and how fast it tracks.

## 🗺️ Roadmap
- [ ] **Phase 1: Detection:** train/fine-tune an object detection model on drone images; measure accuracy and false positives (birds, planes, clouds)
- [ ] **Phase 2: Tracking controller:** convert the drone's pixel offset into pan/tilt commands; tune a PID loop in simulation and on a bench target
- [ ] **Phase 3: Turret hardware:** 3D-printed pan-tilt mount, servos or steppers, camera, onboard computer
- [ ] **Phase 4: Field testing:** track a real drone outdoors; log tracking error, latency, and detection range

## 📈 Progress log
| Date | Milestone | Notes |
|------|-----------|-------|
| 11/04/2026 | Project started | Defined scope and roadmap |
| | | |

## 📊 Results
*Coming soon:* detection accuracy, tracking error over time, and system latency.

## 🧰 Tech stack
- **Software:** Python, OpenCV, YOLO object detection
- **Hardware:** Raspberry Pi / Jetson Nano, camera module, pan-tilt servos, 3D-printed mount
- **CAD:** SolidWorks / Fusion 360

## 📁 Repository structure
```
drone-tracking-turret/
├── detection/    # model training & inference
├── tracking/     # controller code
├── hardware/     # CAD files, wiring diagrams
├── data/         # test logs
├── media/        # photos, videos, plots
└── README.md
```

## 🧠 What I'm learning
<!-- Update as you go: problems you hit and how you solved them. Recruiters read this. -->
- 

## ⚠️ Scope
This is a passive detection and tracking system only. It carries no effector and does not interfere with any aircraft. Drone test flights follow FAA recreational flying rules.

---
*Built by Mat Yohannes · Mechanical Engineering, Howard University*
