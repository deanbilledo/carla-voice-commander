@echo off
echo Starting CARLA Simulator...
cd "C:\Carla-0.10.0-Win64-Shipping"
start CarlaUnreal.exe -windowed -ResX=1920 -ResY=1080
echo CARLA starting... Please wait for the 3D world to load, then run the Python simulation.
pause
