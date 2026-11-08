"""Signal-strength meter widgets."""

from math import isfinite
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QSlider, QVBoxLayout, QWidget


class Meter(QWidget):
    """Slider-based meter retained for compatibility with the original UI."""

    def __init__(self, values: list, current_value: int, avg: int):
        super().__init__()
        self.values = values
        self.current_value = current_value
        self.avg = avg
        self.initUI()

    def initUI(self):
        project_dir = Path(__file__).parent
        css_path = project_dir / "meter.css"
        if css_path.is_file():
            self.setStyleSheet(css_path.read_text(encoding="utf-8"))
        self.setWindowTitle("LinuxLog | meter")
        self.setWindowIcon(QIcon(str(project_dir / "logo.png")))
        self.meter_slider = QSlider(Qt.Orientation.Horizontal)
        self.meter_slider.setFixedHeight(30)
        self.meter_slider.setRange(1, 100)
        self.meter_slider.setStyleSheet("QSlider{ background: #000000}")
        self.set_current_value(self.current_value)
        self.meter_label = QLabel(" | ".join(map(str, self.values)))
        layout = QVBoxLayout(self)
        layout.addWidget(self.meter_slider)
        layout.addWidget(self.meter_label)

    def set_s_meter(self, dBm):
        self.set_current_value(self.dBm_to_value(dBm))

    @staticmethod
    def dBm_to_value(level_s):
        """Map the historical -121..-13 dBm range onto 0..100."""
        level = float(level_s)
        if not isfinite(level):
            return 0
        return (level + 121.0) / 108.0 * 100

    def set_current_value(self, value):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 1
        if not isfinite(numeric_value):
            numeric_value = 1
        self.current_value = max(1, min(100, round(numeric_value)))
        self.meter_slider.setSliderPosition(self.current_value)


class CustomMeter(QWidget):
    """Painted meter whose contents survive normal Qt repaint events."""

    def __init__(self):
        super().__init__()
        self.resize(300, 100)
        self.setWindowTitle("Custom Meter")
        self._level = 0

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_y = self.height() // 2
        margin = 8
        end_x = margin + round(max(0, self.width() - 2 * margin) * self._level / 100)
        painter.setPen(QPen(self.palette().color(self.foregroundRole()), 3))
        painter.drawLine(margin, center_y, end_x, center_y)

    def set_s_meter(self, dBm):
        self._level = max(0, min(100, self.dBm_to_value(dBm)))
        self.update()

    @staticmethod
    def dBm_to_value(level_s):
        level = float(level_s)
        if not isfinite(level):
            return 0
        return round((level + 121.0) / 108.0 * 100)
