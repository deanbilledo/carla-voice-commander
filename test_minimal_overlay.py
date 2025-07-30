#!/usr/bin/env python3
"""
🚗 Webots Overlay Test Launcher - Minimal Version
Test the overlay interface without GeminiAgent to debug the closing issue
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class MinimalOverlay(QFrame):
    """Minimal test overlay"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 230);
                border: 2px solid rgba(100, 100, 100, 150);
                border-radius: 15px;
            }
            QPushButton {
                background: rgba(240, 240, 240, 200);
                color: black;
                border: 1px solid gray;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QLabel {
                color: black;
                font-weight: bold;
            }
        """)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🚗 MINIMAL OVERLAY TEST")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        status = QLabel("✅ Overlay is running successfully!")
        status.setAlignment(Qt.AlignCenter)
        layout.addWidget(status)
        
        close_btn = QPushButton("✖️ Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

def main():
    """Minimal test launcher"""
    print("🚗 Minimal Overlay Test")
    print("=" * 30)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        print("✅ Creating minimal overlay...")
        
        # Create minimal overlay
        overlay = MinimalOverlay()
        overlay.show()
        
        print("✅ Overlay shown - should stay open now")
        print("💡 If this works, the issue is with GeminiAgent import")
        
        # Run the application
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
