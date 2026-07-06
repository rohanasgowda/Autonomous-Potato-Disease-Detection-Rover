# 🚜 Autonomous Potato Disease Detection Rover

An edge-based autonomous agricultural rover for **real-time potato leaf disease detection, disease severity estimation, AI-assisted treatment recommendation, and precision crop monitoring** using **Raspberry Pi 5**, **TensorFlow Lite**, **FastAPI**, and **MobileNetV3**.

---

## 📌 Project Overview

Plant diseases significantly reduce crop yield and quality, while manual monitoring is time-consuming and often inaccurate. This project presents an **Autonomous Potato Disease Detection Rover** capable of navigating crop fields, capturing leaf images, identifying diseases using a lightweight deep learning model, estimating disease severity, and providing intelligent treatment recommendations.

The complete system combines **edge AI, computer vision, backend analytics, and decision support** into a unified precision agriculture platform.

---

# ✨ Features

- 🌱 Real-time Potato Leaf Disease Detection
- 🤖 Lightweight MobileNetV3 Model
- ⚡ TensorFlow Lite Edge Deployment
- 🚜 Raspberry Pi 5 Autonomous Rover
- 📷 Camera-based Leaf Image Acquisition
- 📊 Disease Severity Estimation
- 🗺 Interactive Disease Heatmap
- 🧠 AI-generated Treatment Recommendation
- 💊 Vendor Inventory Assistance
- 📩 Telegram Notification System
- 💾 FastAPI Backend
- 🗄 SQLite Database Integration
- 🌐 Interactive Dashboard
- 📈 Real-time Monitoring

---

# 🏗 System Architecture

```text
                      Raspberry Pi 5 Rover
                              │
                              ▼
                     Camera Image Capture
                              │
                              ▼
                MobileNetV3 + TensorFlow Lite
                              │
          ┌───────────────────┴──────────────────┐
          ▼                                      ▼
 Disease Classification              Severity Estimation
          │                                      │
          └──────────────┬───────────────────────┘
                         ▼
                  FastAPI Backend
                         │
         ┌───────────────┼─────────────────┐
         ▼               ▼                 ▼
     SQLite DB      Heatmap          OpenRouter AI
                                         │
                                         ▼
                           Treatment Recommendation
                                         │
                                         ▼
                              Telegram Notification
```

---

# 🧠 AI Model

| Parameter | Value |
|------------|--------|
| Model | MobileNetV3 |
| Framework | TensorFlow |
| Deployment | TensorFlow Lite |
| Platform | Raspberry Pi 5 |
| Classes | Healthy, Early Blight, Late Blight |
| Transfer Learning | ImageNet |

---

# 📊 Experimental Results

| Metric | Value |
|---------|-------|
| Accuracy | **97.63%** |
| Weighted F1 Score | **97.65%** |
| Average Inference Time | **10.99 ms** |
| Deployment | Raspberry Pi 5 |

The proposed framework demonstrates excellent classification accuracy while maintaining low computational complexity suitable for edge deployment.

---

# 🔄 Workflow

1. Rover navigates through the crop field.
2. Camera captures potato leaf image.
3. TensorFlow Lite performs inference.
4. Disease is classified.
5. Severity percentage is estimated.
6. Detection is stored in backend.
7. Heatmap is updated.
8. OpenRouter generates treatment recommendation.
9. Vendor inventory is retrieved.
10. Telegram notification is sent.

---

# 💻 Technology Stack

## Hardware

- Raspberry Pi 5
- Pi Camera
- DC Motors
- Motor Driver
- Chassis
- Battery Pack

## Software

- Python
- TensorFlow
- TensorFlow Lite
- FastAPI
- SQLite
- OpenRouter API
- Telegram Bot API
- HTML
- CSS
- JavaScript

---

# 📁 Repository Structure

```text
Autonomous-Potato-Disease-Detection-Rover
│
├── backend/
├── docs/
├── heatmap_dashboard/
├── phase3/
├── phase4/
├── phase6/
├── phase7/
├── README.md
└── .gitignore
```

---

# 📂 Module Description

## Backend

- FastAPI REST APIs
- SQLite Integration
- Dashboard APIs
- Recommendation APIs
- Inventory APIs
- Notification APIs

---

## Phase 3

- OpenRouter Integration
- Telegram Notification
- Recommendation Engine
- Backend Communication

---

## Phase 4

- Model Training
- Data Augmentation
- TensorFlow Lite Export
- Severity Estimation
- Model Evaluation

---

## Phase 6

- Raspberry Pi Deployment
- Camera Interface
- Rover Control
- Image Capture Pipeline
- Field Workflow

---

## Dashboard

- Disease Statistics
- Heatmap Visualization
- Detection History
- Recommendation Display

---

# 📈 Disease Severity Estimation

The proposed framework estimates the percentage of infected leaf area using image processing techniques, enabling quantitative disease assessment rather than simple disease classification.

---

# 🤖 AI Recommendation Engine

Following disease detection, the system automatically generates:

- Disease Description
- Probable Cause
- Preventive Measures
- Fungicide Recommendation
- Organic Treatment
- Crop Management Guidelines

---

# 📩 Telegram Notification

The system sends real-time notifications containing:

- Disease Name
- Severity Percentage
- Treatment Recommendation
- Detection Timestamp

---

# 🌍 Applications

- Precision Agriculture
- Smart Farming
- Disease Monitoring
- Crop Health Assessment
- Agricultural Research
- IoT-based Farming

---

# 🚀 Future Scope

- Autonomous Path Planning
- Multi-Crop Disease Detection
- Drone Integration
- Cloud Synchronization
- Multi-Language Support
- Weather-aware Recommendations
- IoT Sensor Fusion
- Large-scale Farm Deployment

---

# 📷 Demo

> Screenshots and demonstration images will be added here.

- Rover
- Dashboard
- Heatmap
- Disease Detection
- Telegram Notification

---

# 📖 Research Contribution

This project demonstrates the integration of:

- Edge AI
- Embedded Systems
- Computer Vision
- Precision Agriculture
- IoT
- Intelligent Decision Support

into a unified autonomous agricultural platform suitable for real-world deployment.

---

# 👨‍💻 Team

Department of Electronics and Communication Engineering

JSS Science and Technology University, Mysuru

---

# ⭐ Support

If you found this project useful, consider giving the repository a ⭐ on GitHub.

---

# 📜 License

This project is developed for academic and research purposes.
