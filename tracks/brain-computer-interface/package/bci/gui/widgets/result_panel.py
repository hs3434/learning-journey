"""
Result Panel
============
Displays decoding results: accuracy, confusion matrix, stream predictions.
"""
from __future__ import annotations
from typing import Optional
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt


class ResultPanel(QWidget):
    """Decoding results display panel.

    Supports batch mode (accuracy + confusion matrix) and stream mode
    (real-time prediction labels).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._title = QLabel("Results")
        self._title.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self._title)

        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setStyleSheet(
            "background-color: #2d2d2d; color: #00ff88; font-family: monospace;"
        )
        layout.addWidget(self._content)

        self._prediction_label = QLabel("Prediction: --")
        self._prediction_label.setStyleSheet("color: #88ccff; font-size: 14px;")
        self._prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._prediction_label)

    def update_batch(self, accuracy: float,
                     confusion: Optional[np.ndarray] = None,
                     method: str = ""):
        """Display batch decoding results."""
        lines = [f"Method: {method}", f"Accuracy: {accuracy:.3f}"]
        if confusion is not None:
            lines.append("")
            lines.append("Confusion Matrix:")
            for row in confusion:
                lines.append("  " + " ".join(f"{v:5.0f}" for v in row))
        self._content.setText("\n".join(lines))
        self._prediction_label.setText("")

    def update_stream(self, label: str):
        """Display real-time classification prediction."""
        self._prediction_label.setText(f"Prediction: {label}")

    def clear(self):
        """Clear all displayed results."""
        self._content.clear()
        self._prediction_label.setText("Prediction: --")
