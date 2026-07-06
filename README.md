<div align="center">

# 🚜 Autonomous Potato Disease Detection Rover

![Stars](https://img.shields.io/github/stars/rohanasgowda/Autonomous-Potato-Disease-Detection-Rover?style=social)

![Forks](https://img.shields.io/github/forks/rohanasgowda/Autonomous-Potato-Disease-Detection-Rover?style=social)

### Edge-Based Precision Agriculture Platform for Real-Time Disease Detection, Severity Estimation, and Intelligent Crop Management

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange?logo=tensorflow)
![TensorFlow Lite](https://img.shields.io/badge/TensorFlow-Lite-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red?logo=raspberrypi)
![MobileNetV3](https://img.shields.io/badge/Model-MobileNetV3-success)
![License](https://img.shields.io/badge/License-Academic-blue)

---

**An intelligent edge-based agricultural rover capable of autonomous crop monitoring, real-time potato leaf disease detection, disease severity estimation, AI-assisted treatment recommendation, and precision farming support using Raspberry Pi 5, TensorFlow Lite, FastAPI, and MobileNetV3.**

</div>

---

# 🌱 Overview

Plant diseases are one of the major causes of reduced agricultural productivity worldwide. Traditional disease monitoring methods rely heavily on manual inspection, which is time-consuming, labor-intensive, and often inaccurate for large-scale farms.

This project presents an **Autonomous Potato Disease Detection Rover**, an intelligent edge-computing platform designed to automatically monitor potato crops and assist farmers in disease diagnosis and treatment planning.

Unlike conventional image classification systems, the proposed framework extends beyond disease detection by integrating:

- Real-time edge AI inference
- Disease severity estimation
- Intelligent treatment recommendation
- Interactive disease heatmap
- Backend analytics
- Telegram notification system
- Inventory management support
- Precision agriculture dashboard

The complete system has been optimized for deployment on **Raspberry Pi 5**, enabling efficient operation with low computational overhead while maintaining high prediction accuracy.

---

# 🎯 Objectives

The primary objectives of this project are:

- Develop an autonomous agricultural rover for field monitoring.
- Detect potato leaf diseases in real time.
- Deploy a lightweight deep learning model on Raspberry Pi 5.
- Estimate disease severity using image processing.
- Provide AI-generated treatment recommendations.
- Generate disease heatmaps for crop monitoring.
- Store disease records using a backend database.
- Notify users through Telegram.
- Build an interactive dashboard for visualization.
- Demonstrate a complete edge AI precision agriculture platform.

---

# ✨ Key Features

## 🌿 Disease Detection

- Real-time potato leaf disease classification
- Healthy, Early Blight and Late Blight detection
- TensorFlow Lite optimized inference
- MobileNetV3 lightweight architecture

---

## 🚜 Autonomous Rover

- Raspberry Pi 5 based deployment
- Camera-based image acquisition
- Autonomous crop monitoring workflow
- Edge AI inference

---

## 📊 Disease Severity Estimation

- Calculates percentage of infected leaf area
- Helps prioritize treatment
- Supports precision agriculture

---

## 🤖 AI-Assisted Decision Support

- Intelligent treatment recommendation
- Disease description
- Preventive measures
- Fungicide recommendation
- Organic treatment suggestion
- Crop management guidelines

---

## 📩 Telegram Notifications

Automatic notification including:

- Disease name
- Severity percentage
- Treatment recommendation
- Detection timestamp

---

## 🗺 Interactive Dashboard

- Disease statistics
- Detection history
- Heatmap visualization
- Severity monitoring
- Backend analytics

---

## 💾 Backend Integration

- FastAPI REST APIs
- SQLite database
- Inventory management
- Recommendation services
- Dashboard APIs

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
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
 Disease Classification           Severity Estimation
         │                                   │
         └──────────────┬────────────────────┘
                        ▼
                 FastAPI Backend
                        │
      ┌─────────────────┼──────────────────┐
      ▼                 ▼                  ▼
 SQLite Database   Heatmap Dashboard   OpenRouter AI
                                              │
                                              ▼
                              Treatment Recommendation
                                              │
                                              ▼
                                   Telegram Notification
```

---

# 🔄 Complete Workflow

1. Rover navigates through the agricultural field.
2. Camera captures potato leaf images.
3. TensorFlow Lite performs disease classification.
4. Disease severity is estimated.
5. Detection information is stored in the backend.
6. Dashboard updates automatically.
7. Heatmap visualizes infected regions.
8. OpenRouter generates treatment recommendations.
9. Telegram sends instant notification.
10. Farmers receive actionable insights for disease management.

---

# 🛠 Technology Stack

## Hardware

- Raspberry Pi 5
- Raspberry Pi Camera Module
- DC Motors
- Motor Driver
- Battery Pack
- Rover Chassis

---

## Software

- Python
- TensorFlow
- TensorFlow Lite
- FastAPI
- SQLite
- HTML
- CSS
- JavaScript
- OpenRouter API
- Telegram Bot API

---

# 🧠 Deep Learning Model

| Parameter | Value |
|------------|--------|
| Model | MobileNetV3 |
| Framework | TensorFlow |
| Deployment | TensorFlow Lite |
| Transfer Learning | ImageNet |
| Classes | Healthy, Early Blight, Late Blight |
| Platform | Raspberry Pi 5 |
| Inference | Real-Time |

---

# 📊 Performance Summary

| Metric | Value |
|---------|-------|
| Classification Accuracy | **97.63%** |
| Weighted F1 Score | **97.65%** |
| Average Inference Time | **10.99 ms** |
| Deployment Platform | Raspberry Pi 5 |
| Disease Classes | 3 |

---
# 📂 Repository Structure

```text
Autonomous-Potato-Disease-Detection-Rover
│
├── backend/                 # FastAPI Backend
├── docs/                    # Documentation
├── heatmap_dashboard/       # Dashboard UI
├── phase3/                  # AI Recommendation Engine
├── phase4/                  # Model Training & TFLite Export
├── phase6/                  # Raspberry Pi Deployment
├── phase7/                  # Final Documentation
├── images/                  # Project Images
├── README.md
└── .gitignore
```

---

# 🚜 Hardware Prototype

The complete rover was designed as a lightweight edge-computing platform capable of autonomous field monitoring and real-time disease diagnosis.

<p align="center">
<img src="images/hardware3.jpg" width="700"/>
</p>

### Additional Views

<p align="center">
<img src="images/hardware1.jpg" width="350"/>
<img src="images/hardware2.jpg" width="350"/>
</p>

---

# 🏗 Proposed System Architecture

<p align="center">
<img src="images/fig1.png" width="800"/>
</p>

The proposed architecture combines edge computing, lightweight deep learning, backend analytics, AI-assisted recommendation generation and dashboard visualization into a unified precision agriculture framework.

---

# 🔄 Overall Workflow

<p align="center">
<img src="images/fig6.png" width="800"/>
</p>

The workflow begins with image acquisition on Raspberry Pi and continues through disease classification, severity estimation, backend storage, AI recommendation generation and dashboard visualization.

---

# 📊 Training Performance

## Training Accuracy

<p align="center">
<img src="images/accuracy_plot.png" width="700"/>
</p>

The MobileNetV3 model demonstrates stable convergence with both training and validation accuracy exceeding 97%.

---

## Training Loss

<p align="center">
<img src="images/loss_plot.png" width="700"/>
</p>

The loss curves indicate effective optimization and minimal overfitting throughout training.

---

# 📈 Confusion Matrix

<p align="center">
<img src="images/confusion matrix.png" width="650"/>
</p>

The classifier successfully distinguishes among Healthy, Early Blight and Late Blight leaves with excellent class-wise performance.

---

# 📉 Precision–Recall Curve

<p align="center">
<img src="images/precision_recall_curve.png" width="700"/>
</p>

The precision–recall curves remain close to the upper-right corner, demonstrating excellent confidence across all disease classes.

---

# 🍃 Disease Detection Examples

## Healthy Leaf

<p align="center">

<img src="images/original (1121).jpg" width="250"/>

↓

<img src="images/10healthy.png" width="650"/>

</p>

The system correctly classifies healthy potato leaves and reports zero disease severity.

---

## Early Blight Detection

<p align="center">

<img src="images/early (852).jpg" width="250"/>

↓

<img src="images/10early_blight.png" width="650"/>

</p>

The system detects Early Blight and estimates disease severity before generating treatment recommendations.

---

## Late Blight Detection

<p align="center">

<img src="images/late_blight (702).jpg" width="250"/>

↓

<img src="images/10late_blight.png" width="650"/>

</p>

Late Blight samples are accurately classified with severity estimation and backend logging.

---

# 🗺 Disease Heatmap

<p align="center">
<img src="images/fig9a.png" width="700"/>
</p>

The dashboard generates an interactive disease heatmap representing disease severity across different plants, enabling localized treatment and precision pesticide application.

---

# 💻 Dashboard

<p align="center">
<img src="images/fig7a.png" width="750"/>
</p>

The FastAPI backend stores every detection and presents disease statistics through an interactive dashboard.

---

<p align="center">
<img src="images/fig7b.png" width="750"/>
</p>

The dashboard also provides visualization of disease trends and monitoring history.

---

# 📑 Project Pipeline

<p align="center">
<img src="images/fig2.png" width="500"/>
</p>

---

<p align="center">
<img src="images/fig4.png" width="600"/>
</p>

---

<p align="center">
<img src="images/fig5.png" width="600"/>
</p>

These diagrams illustrate the complete processing pipeline from image acquisition to AI-assisted crop management.

---
# ⚙ Backend Architecture

The backend is developed using **FastAPI**, providing a lightweight and high-performance REST API framework for communication between the Raspberry Pi rover, AI recommendation engine, dashboard, and database.

## Backend Responsibilities

- Disease record management
- Detection history
- Dashboard APIs
- Heatmap generation
- Inventory management
- AI recommendation integration
- Telegram notification service
- SQLite database interaction

---

# 🗄 Database Management

The proposed system uses **SQLite** for lightweight local storage.

Each detection record stores:

- Timestamp
- Disease Name
- Disease Severity
- Plant Location
- Confidence Score
- Image Path
- Recommendation Status
- Notification Status

The database enables efficient retrieval of historical disease records for visualization and analysis.

---

# 🤖 AI Recommendation Engine

Unlike conventional disease detection systems, this project integrates an AI-powered decision support framework using the **OpenRouter API**.

Following disease detection, the recommendation engine automatically generates:

- Disease Description
- Probable Cause
- Preventive Measures
- Chemical Treatment
- Organic Treatment
- Fungicide Recommendation
- Crop Management Guidelines
- Farmer-friendly Explanation

This transforms the system from a disease classifier into an intelligent agricultural assistant.

---

# 📩 Telegram Notification System

The system automatically sends Telegram alerts whenever a disease is detected.

Each notification includes:

- 🌿 Disease Name
- 📊 Severity Percentage
- 🎯 Confidence Score
- 💊 Treatment Recommendation
- 🕒 Detection Time

This enables farmers to receive immediate alerts without continuously monitoring the dashboard.

---

# 📊 Disease Severity Estimation

Beyond disease classification, the proposed framework estimates the percentage of infected leaf area.

The severity estimation module:

- Segments infected regions
- Calculates infected area percentage
- Categorizes disease severity
- Supports treatment prioritization

Severity estimation provides significantly more information than simple disease classification.

---

# 🗺 Disease Heatmap

The backend continuously updates a disease heatmap.

Each detected plant is represented by a grid cell whose color intensity corresponds to disease severity.

Benefits include:

- Localized disease monitoring
- Precision pesticide application
- Reduced chemical usage
- Early hotspot identification
- Improved crop management

---

# 🌐 Dashboard Features

The dashboard provides a complete overview of field health.

### Dashboard Modules

- Disease Statistics
- Heatmap Visualization
- Detection History
- Severity Monitoring
- Recommendation Viewer
- Inventory Details
- Backend Status

---

# 📡 REST API Services

The FastAPI backend exposes REST endpoints for seamless communication.

### Detection APIs

- Upload Detection
- Retrieve Detection
- Detection History

### Recommendation APIs

- Generate Recommendation
- View Recommendations

### Dashboard APIs

- Statistics
- Heatmap
- Disease Summary

### Inventory APIs

- Available Products
- Fungicide Information
- Organic Alternatives

### Notification APIs

- Telegram Alerts
- Alert History

---

# 🔬 Model Development

The AI model was developed using transfer learning.

### Training Pipeline

Dataset

↓

Preprocessing

↓

Data Augmentation

↓

Transfer Learning

↓

Model Training

↓

Validation

↓

TensorFlow Lite Conversion

↓

Edge Deployment

---

# 🧪 Experimental Evaluation

The proposed framework was evaluated on an independent potato leaf dataset containing:

- Healthy Leaves
- Early Blight
- Late Blight

The experimental evaluation considered:

- Classification Accuracy
- Precision
- Recall
- F1 Score
- Inference Time
- Edge Deployment Performance

---

# 📈 Experimental Results

| Metric | Value |
|---------|-------|
| Overall Accuracy | **97.63%** |
| Weighted F1 Score | **97.65%** |
| Average Inference Time | **10.99 ms** |
| Deployment Platform | Raspberry Pi 5 |

The proposed MobileNetV3 model demonstrates excellent classification accuracy while maintaining very low computational complexity suitable for embedded deployment.

---

# 🌍 Applications

The developed platform can be applied to:

- Precision Agriculture
- Smart Farming
- Autonomous Crop Monitoring
- Agricultural Research
- Disease Surveillance
- IoT-based Farming
- Precision Pesticide Application
- Large-scale Farm Monitoring

---

# 📖 Research Contribution

The proposed work contributes by integrating:

- Edge Computing
- Lightweight Deep Learning
- TensorFlow Lite
- Embedded AI
- Disease Severity Estimation
- Backend Analytics
- Interactive Dashboard
- AI-assisted Decision Support
- Telegram Notification
- Precision Agriculture

into a single autonomous agricultural platform.

Unlike conventional disease classification systems, the proposed framework extends beyond prediction by providing complete decision support for practical field deployment.

---

# 🚀 Installation Guide

## Prerequisites

Before running the project, ensure the following software is installed:

- Python 3.11+
- Git
- TensorFlow
- FastAPI
- SQLite
- Raspberry Pi OS (for deployment)
- Raspberry Pi Camera Module
- Telegram Bot
- OpenRouter API Key

---

## Clone Repository

```bash
git clone https://github.com/rohanasgowda/Autonomous-Potato-Disease-Detection-Rover.git

cd Autonomous-Potato-Disease-Detection-Rover
```

---

## Install Dependencies

Backend

```bash
cd backend
pip install -r requirements.txt
```

Phase 3

```bash
cd ../phase3
pip install -r requirements.txt
```

Phase 4

```bash
cd ../phase4
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file.

```env
OPENROUTER_API_KEY=YOUR_API_KEY
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
```

---

## Start Backend

```bash
cd backend

uvicorn app.main:app --reload
```

---

## Start Dashboard

Open

```
heatmap_dashboard/index.html
```

or serve using

```bash
python -m http.server
```

---

## Raspberry Pi Deployment

Copy the project to Raspberry Pi.

Run

```bash
python phase6/main.py
```

The rover automatically:

- Captures image
- Performs disease detection
- Estimates severity
- Sends results to backend
- Generates recommendations
- Sends Telegram notification

---

# 📋 Folder Description

| Folder | Description |
|----------|-------------|
| backend | FastAPI backend |
| docs | Documentation |
| heatmap_dashboard | Dashboard UI |
| phase3 | OpenRouter & Telegram Integration |
| phase4 | Model Training & TensorFlow Lite |
| phase6 | Raspberry Pi Deployment |
| phase7 | Final Documentation |

---

# 🧩 Future Improvements

The proposed platform can be extended by integrating:

- 🌍 GPS Navigation
- 🚜 Autonomous Path Planning
- 🛰 Drone Integration
- 🌦 Weather Prediction
- 📡 IoT Sensor Fusion
- 🌱 Multi-crop Disease Detection
- 📲 Mobile Application
- ☁ Cloud Synchronization
- 🤖 Large Language Model Assistance
- 🌐 Remote Farm Monitoring

---

# 📄 Publications

This repository accompanies the research work on intelligent edge-based potato disease detection and precision agriculture.

The developed framework combines:

- Computer Vision
- Embedded Systems
- Deep Learning
- Edge Computing
- Precision Agriculture
- AI-assisted Decision Support

into a unified agricultural monitoring platform.

---

# 👨‍💻 Developers

Department of Electronics and Communication Engineering

**JSS Science and Technology University**

Mysuru, Karnataka, India

---

# 🙏 Acknowledgements

The authors gratefully acknowledge:

- JSS Science and Technology University
- Faculty Members
- Open Source Community
- TensorFlow Team
- FastAPI Developers
- Raspberry Pi Foundation

for providing the tools and ecosystem that made this project possible.

---

# 📜 License

This project is intended for **academic, educational and research purposes**.

For commercial use, permission from the authors is recommended.

---

# ⭐ If you like this project...

Please consider giving this repository a ⭐ on GitHub.

It helps others discover the project and supports future development.

---

<div align="center">

## 🌾 Precision Agriculture through Edge Intelligence

**Made with ❤️ using Raspberry Pi 5, TensorFlow Lite, FastAPI and MobileNetV3**

</div>




