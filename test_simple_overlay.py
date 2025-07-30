#!/usr/bin/env python3
"""
Simple overlay test to debug the closing issue
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt

def test_simple_overlay():
    """Test basic PyQt5 overlay functionality"""
    print("🧪 Testing simple overlay...")
    
    app = QApplication(sys.argv)
    
    # Create a simple test window
    window = QWidget()
    window.setFixedSize(300, 200)
    window.setWindowFlags(Qt.WindowStaysOnTopHint)
    window.setWindowTitle("Test Overlay")
    
    label = QLabel("🎮 Test Overlay Working!\nClose this window to exit.", window)
    label.setAlignment(Qt.AlignCenter)
    label.setGeometry(10, 10, 280, 180)
    
    window.show()
    
    print("✅ Simple overlay shown. Check if it appears and stays open.")
    
    # Run event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_simple_overlay()
