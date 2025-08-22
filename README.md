# Dlib_Kivy_Test
Dlib Kivy Test on Desktop and Android 
Dlib Python Face Detection on Kivy Android
Author: Sk Sahil
GitHub: https://github.com/Sahil-pixel
Date: 22/Aug/2025

Overview:
This is Python Kivy App for Desktop & Android to access the device camera and perform real-time face detection using Dlib. Detected faces are highlighted with bounding boxes.

Features:
- Real-time face detection with Dlib
- Displays number of detected faces
- Supports front and back cameras
- Play/Pause camera stream
- Fully implemented with NumPy (no OpenCV required)

Requirements:
- Python 3.11+
- Kivy
- Dlib
- NumPy ≤ 1.26
- Android device with camera

Usage:
- Run the app: python main.py
- Grant Camera permission on Android
- Use "P/S" button to play/pause camera
- Use "Change Camera" toggle to switch front/back camera

Code Structure:
- CameraWidget: Handles camera feed and texture updates
- CameraApp: Main Kivy app with UI, face detection, and texture processing
- update(): Converts camera texture to NumPy array, detects faces, updates display
- texture_to_numpy(): Converts Kivy texture to grayscale and RGBA

Notes:
- Handles front/back camera rotation and mirroring for Android
- Face detection done on grayscale for speed
- Bounding boxes drawn on Kivy widget canvas

License:
MIT License

