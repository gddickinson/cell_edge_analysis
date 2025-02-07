# src/gui/analysis_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QSpinBox, QPushButton, QComboBox, QCheckBox,
                           QGroupBox)

class IntensityAnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Intensity Analysis Settings")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Sampling Parameters Group
        sampling_group = QGroupBox("Sampling Parameters")
        sampling_layout = QVBoxLayout()

        # Sampling depth
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Sampling Depth (px):"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 100)
        self.depth_spin.setValue(20)
        self.depth_spin.setToolTip("Distance to sample into the cell")
        depth_layout.addWidget(self.depth_spin)
        sampling_layout.addLayout(depth_layout)

        # Vector width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Vector Width (px):"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 50)
        self.width_spin.setValue(5)
        self.width_spin.setToolTip("Width of sampling region")
        width_layout.addWidget(self.width_spin)
        sampling_layout.addLayout(width_layout)

        # Sampling interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Sampling Interval (px):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 100)
        self.interval_spin.setValue(20)
        self.interval_spin.setToolTip("Distance between measurement points")
        interval_layout.addWidget(self.interval_spin)
        sampling_layout.addLayout(interval_layout)

        sampling_group.setLayout(sampling_layout)
        layout.addWidget(sampling_group)

        # Vector Direction Group
        direction_group = QGroupBox("Vector Direction Control")
        direction_layout = QVBoxLayout()

        # Normal window settings
        normal_layout = QHBoxLayout()
        normal_layout.addWidget(QLabel("Normal Calculation Window:"))
        self.normal_spin = QSpinBox()
        self.normal_spin.setRange(3, 21)
        self.normal_spin.setValue(5)
        self.normal_spin.setSingleStep(2)
        self.normal_spin.setToolTip("Window size for calculating normal vectors (must be odd)")
        normal_layout.addWidget(self.normal_spin)
        direction_layout.addLayout(normal_layout)

        # Interior check settings
        check_layout = QVBoxLayout()
        self.interior_check = QCheckBox("Enable Interior Check")
        self.interior_check.setChecked(True)
        self.interior_check.setToolTip("Verify vector direction points into cell")
        check_layout.addWidget(self.interior_check)

        check_params_layout = QHBoxLayout()
        check_params_layout.addWidget(QLabel("Check Depth (px):"))
        self.check_depth_spin = QSpinBox()
        self.check_depth_spin.setRange(5, 50)
        self.check_depth_spin.setValue(10)
        self.check_depth_spin.setToolTip("Distance to check for cell interior")
        check_params_layout.addWidget(self.check_depth_spin)

        check_params_layout.addWidget(QLabel("Check Points:"))
        self.check_points_spin = QSpinBox()
        self.check_points_spin.setRange(5, 20)
        self.check_points_spin.setValue(10)
        self.check_points_spin.setToolTip("Number of points to check along vector")
        check_params_layout.addWidget(self.check_points_spin)
        check_layout.addLayout(check_params_layout)

        direction_layout.addLayout(check_layout)
        direction_group.setLayout(direction_layout)
        layout.addWidget(direction_group)

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
        # Ensure normal window size is odd
        normal_window = self.normal_spin.value()
        if normal_window % 2 == 0:
            normal_window += 1

        return {
            'sampling_depth': self.depth_spin.value(),
            'vector_width': self.width_spin.value(),
            'sampling_interval': self.interval_spin.value(),
            'measure_type': self.measure_combo.currentText().lower(),
            'normal_window': normal_window,
            'use_interior_check': self.interior_check.isChecked(),
            'check_depth': self.check_depth_spin.value(),
            'check_points': self.check_points_spin.value()
        }
