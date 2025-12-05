# Aim Calibration & Trainer — README

## 📌 Overview

The **Aim Calibration & Trainer** is a standalone Python application designed to help players improve their aim, sensitivity settings, and muscle memory across multiple shooter games. It provides flexible modes, controller support, first-person/third-person perspectives, short-range/long-range target options, and an infinite aim-trainer mode.

This tool **does not modify any game** and is **not an aimbot**. It is purely for personal skill development.

---

## 🎯 Features

### ✔ First-Person (FPS) & Third-Person (TPP) Modes

Switch between realistic crosshair styles to match the games you play.

### ✔ Full Controller Support

Uses right-stick input for aiming with adjustable controller sensitivity.
Supports Xbox, PlayStation, and most general gamepads recognized by Pygame.

### ✔ Multi-Game Sensitivity Profiles

Included presets for:

* Valorant
* Fortnite
* Warzone
* CS2
* Apex Legends

Each preset includes recommended starting points + beginner-friendly aim tips.

### ✔ Short-Range & Long-Range Training Targets

* **Short Range:** tighter targets, slower movement, precision-focused
* **Long Range:** wider targets, faster movement, speed/tracking focus

### ✔ Infinite Aim Trainer

The trainer can stay active forever until closed by the user.
Great for warming up before gaming sessions.

### ✔ Sensitivity Calibration

The app helps you:

* Find your ideal mouse sensitivity
* Tune controller look speed
* Understand precision vs speed trade-offs

---

## 🕹 Controls

### **General Controls**

| Key     | Action                                     |
| ------- | ------------------------------------------ |
| **P**   | Toggle FPS/TPP mode                        |
| **G**   | Cycle through game profiles                |
| **R**   | Toggle short/long range targets            |
| **T**   | Start/stop the regular trainer             |
| **I**   | Start/stop the infinite trainer            |
| **↑/↓** | Increase/decrease *mouse* sensitivity      |
| **←/→** | Increase/decrease *controller* sensitivity |

### **Controller (if connected)**

| Control     | Action             |
| ----------- | ------------------ |
| Right Stick | Aim / move reticle |

---

## 📦 Requirements

* Python 3.8+
* `pygame` library

Install Pygame with:

```bash
pip install pygame matplotlib
```

---

## ▶ Running the Program

Run the Python file normally:

```bash
python aim_calibrator.py
```

---

## 🧠 Improvement Tips (Included in App)

* Lower sensitivity improves precision.
* Higher sensitivity improves turning speed.
* Try to hit 80–90% of targets at your chosen distance.
* Use short-range mode for micro-flicks.
* Use long-range mode for tracking improvements.
* Stick to a sensitivity for several days before making changes.

---

## 📘 Legal & Safety Notice

This tool is:

* **NOT** an aimbot
* **NOT** a cheat
* **NOT** reading or modifying any game files or memory

Only provides training scenarios on your desktop for legitimate practice.

---

## 📥 Future Updates (Possible)

* Weapon recoil models
* Sensitivity converters between games
* Multiple moving target types
* Hit-accuracy statistics panel
* Menu UI with mouse navigation

If you'd like any of these added, just ask!

---

## 🤝 Credits

Developed using **Python** and **Pygame**.
Optimized for players of all major FPS/TPS titles.

Enjoy improving your aim!
