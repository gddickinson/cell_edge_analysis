# src/gui/analysis_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QSpinBox, QPushButton, QComboBox)

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
        self.depth_spin.setRange(1, 1000)  # Increased range
        self.depth_spin.setValue(20)
        self.depth_spin.setToolTip("Distance to sample into the cell")
        depth_layout.addWidget(self.depth_spin)
        layout.addLayout(depth_layout)

        # Vector width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Vector Width (px):"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(5)
        self.width_spin.setToolTip("Width of sampling region")
        width_layout.addWidget(self.width_spin)
        layout.addLayout(width_layout)

        # Sampling interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Sampling Interval (px):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1000)
        self.interval_spin.setValue(5)
        self.interval_spin.setToolTip("Distance between measurement points")
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # Intensity measure type
        measure_layout = QHBoxLayout()
        measure_layout.addWidget(QLabel("Intensity Measure:"))
        self.measure_combo = QComboBox()
        self.measure_combo.addItems(["Mean", "Minimum", "Maximum"])
        self.measure_combo.setToolTip("Type of intensity measurement to use")
        measure_layout.addWidget(self.measure_combo)
        layout.addLayout(measure_layout)

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
            'vector_width': self.width_spin.value(),
            'sampling_interval': self.interval_spin.value(),
            'measure_type': self.measure_combo.currentText().lower()
        }
