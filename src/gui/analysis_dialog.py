# src/gui/analysis_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QPushButton)

class IntensityAnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Intensity Analysis Settings")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Sampling depth
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Sampling Depth (px):"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 50)
        self.depth_spin.setValue(10)
        self.depth_spin.setToolTip("Distance to sample into the cell")
        depth_layout.addWidget(self.depth_spin)
        layout.addLayout(depth_layout)
        
        # Sampling interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Sampling Interval (px):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 20)
        self.interval_spin.setValue(5)
        self.interval_spin.setToolTip("Distance between measurement points")
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def get_settings(self):
        """Get the dialog settings."""
        return {
            'sampling_depth': self.depth_spin.value(),
            'sampling_interval': self.interval_spin.value()
        }
