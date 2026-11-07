"""World map widget showing Maidenhead locators and the distance to a station."""

from __future__ import annotations

import datetime
import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QLabel, QPushButton, QSlider, QToolTip, QVBoxLayout, QWidget

from qth_locator import (
    bearing_deg,
    distance_km,
    great_circle_points,
    locator_to_latlon,
    normalize_locator,
)
from world_borders import WORLD_BORDERS
from world_cities import WORLD_CITIES
from world_land import WORLD_LAND_POLYGONS
from world_mountains import WORLD_MOUNTAINS


class QTHMapWidget(QWidget):
    cluster_spot_clicked = pyqtSignal(str, str)
    """An equirectangular world map with a Maidenhead field grid."""

    OCEAN_COLOR = QColor(1, 11, 55)
    LAND_COLOR = QColor(64, 119, 76)
    LAND_BORDER_COLOR = QColor(78, 118, 86)
    GRID_COLOR = QColor(95, 133, 172, 15)
    GRID_LABEL_COLOR = QColor(158, 188, 220, 100)
    TEXT_COLOR = QColor(236, 243, 250)
    MUTED_TEXT_COLOR = QColor(178, 198, 220)
    MY_COLOR = QColor(59, 201, 121)
    STATION_COLOR = QColor(240, 92, 84)
    LINE_COLOR = QColor(250, 205, 80)

    def __init__(self, settings_dict=None, parent=None):
        super().__init__(parent)
        self.settings_dict = settings_dict or {}
        self.my_locator = ""
        self.station_call = ""
        self.station_locator = ""
        self.station_source = ""
        self._zoom = 1.0
        self._view = (0.0, 0.0, 360.0, 180.0)
        self._cluster_map_enabled = False
        self._cluster_spots = []
        self.setMouseTracking(True)
        self.setMinimumSize(620, 330)

    def set_cluster_map_enabled(self, enabled):
        self._cluster_map_enabled = bool(enabled)
        self.update()

    def add_cluster_spot(self, call, locator, worked=False, freq=""):
        locator = normalize_locator(locator)
        if not locator:
            return
        try:
            lat, lon = locator_to_latlon(locator)
        except (TypeError, ValueError):
            return
        now = datetime.datetime.now()
        # Replace an existing spot for the same callsign.
        self._cluster_spots = [
            spot for spot in self._cluster_spots if spot["call"] != call
        ]
        self._cluster_spots.append(
            {
                "call": str(call or "").strip().upper(),
                "locator": locator,
                "lat": lat,
                "lon": lon,
                "worked": bool(worked),
                "freq": str(freq or "").strip(),
                "time": now,
            }
        )
        self._prune_cluster_spots()
        if self._cluster_map_enabled:
            self.update()

    def _prune_cluster_spots(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=15)
        self._cluster_spots = [
            spot for spot in self._cluster_spots if spot["time"] >= cutoff
        ]

    def clear_cluster_spots(self):
        self._cluster_spots.clear()
        self.update()

    def mark_cluster_spot_worked(self, call):
        call = str(call or "").strip().upper()
        if not call:
            return
        base = call.split("/")[0]
        changed = False
        for spot in self._cluster_spots:
            spot_base = str(spot.get("call") or "").upper().split("/")[0]
            if spot_base == base and not spot["worked"]:
                spot["worked"] = True
                changed = True
        if changed and self._cluster_map_enabled:
            self.update()

    def _nearest_cluster_spot(self, pos):
        if not self._cluster_map_enabled:
            return None
        rect = self._map_rect()
        if rect.isEmpty():
            return None
        best = None
        best_dist = 10.0
        for spot in self._cluster_spots:
            try:
                point = self._to_point(rect, spot["lat"], spot["lon"])
            except (TypeError, ValueError):
                continue
            dx = point.x() - pos.x()
            dy = point.y() - pos.y()
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best = spot
        return best

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return
        spot = self._nearest_cluster_spot(event.pos())
        if spot is not None:
            self.cluster_spot_clicked.emit(spot["call"], spot.get("freq", ""))

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self._cluster_map_enabled:
            QToolTip.hideText()
            return
        spot = self._nearest_cluster_spot(event.pos())
        if spot is not None:
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"{spot['call']} ({'worked' if spot['worked'] else 'not worked'})",
                self,
            )
        else:
            QToolTip.hideText()
        self.set_my_locator(self.settings_dict.get("my-qth-locator", ""))

    def sizeHint(self):
        return QSize(900, 470)

    def set_my_locator(self, locator):
        locator = normalize_locator(locator)
        if locator != self.my_locator:
            self.my_locator = locator
            self.update()

    def set_station(self, call, locator, source=""):
        call = str(call or "").strip().upper()
        locator = normalize_locator(locator)
        source = str(source or "").strip()
        if (call, locator, source) != (
            self.station_call,
            self.station_locator,
            self.station_source,
        ):
            self.station_call = call
            self.station_locator = locator
            self.station_source = source
            self.update()

    def clear_station(self):
        self.set_station("", "", "")

    def zoom_in(self):
        self._zoom = min(8.0, self._zoom * 1.25)
        self.update()

    def zoom_out(self):
        self._zoom = max(0.5, self._zoom / 1.25)
        self.update()

    def reset_zoom(self):
        self._zoom = 1.0
        self.update()

    def _map_rect(self):
        outer = QRectF(self.rect())
        if self._view != (0.0, 0.0, 360.0, 180.0) or self._zoom != 1.0:
            available = outer.adjusted(0.0, 0.0, 0.0, 0.0)
        else:
            available = outer.adjusted(26.0, 18.0, -10.0, -10.0)
        if available.width() <= 1.0 or available.height() <= 1.0:
            return QRectF()
        width = available.width()
        height = width / 2.0
        if height > available.height():
            height = available.height()
            width = height * 2.0
        left = available.left() + (available.width() - width) / 2.0
        top = available.top() + (available.height() - height) / 2.0
        return QRectF(left, top, width, height)

    def _update_view(self, rect):
        if not self.my_locator or not self.station_locator:
            self._view = (0.0, 0.0, 360.0, 180.0)
            return
        try:
            my_lat, my_lon = locator_to_latlon(self.my_locator)
            station_lat, station_lon = locator_to_latlon(self.station_locator)
            points = great_circle_points(my_lat, my_lon, station_lat, station_lon, steps=48)
        except (TypeError, ValueError):
            self._view = (0.0, 0.0, 360.0, 180.0)
            return
        lons = [point[1] for point in points] + [my_lon, station_lon]
        lats = [point[0] for point in points] + [my_lat, station_lat]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        span_lon = max(1.0, (max_lon - min_lon) * 2.5 / self._zoom)
        span_lat = max(1.0, (max_lat - min_lat) * 2.5 / self._zoom)
        # Keep the map flat: preserve the 2:1 aspect ratio of the widget.
        if span_lon / span_lat < 2.0:
            span_lon = span_lat * 2.0
        elif span_lon / span_lat > 2.0:
            span_lat = span_lon / 2.0
        span_lon = min(360.0, span_lon)
        span_lat = min(180.0, span_lat)
        center_lon = (min_lon + max_lon) / 2.0
        center_lat = (min_lat + max_lat) / 2.0
        self._view = (center_lon, center_lat, span_lon, span_lat)

    def _to_point(self, rect, latitude, longitude):
        center_lon, center_lat, span_lon, span_lat = self._view
        lon = float(longitude)
        while lon - center_lon > 180.0:
            lon -= 360.0
        while center_lon - lon > 180.0:
            lon += 360.0
        x = rect.left() + (lon - (center_lon - span_lon / 2.0)) / span_lon * rect.width()
        y = rect.top() + ((center_lat + span_lat / 2.0) - float(latitude)) / span_lat * rect.height()
        return QPointF(x, y)

    def _land_segments(self, ring, rect):
        segments = []
        segment = []
        previous_longitude = None
        previous_point = None
        for longitude, latitude in ring:
            point = self._to_point(rect, latitude, longitude)
            if previous_longitude is not None and (
                abs(longitude - previous_longitude) > 180.0
                or (previous_point is not None and abs(point.x() - previous_point.x()) > rect.width() / 2.0)
            ):
                if len(segment) >= 3:
                    segments.append(QPolygonF(segment))
                segment = []
            segment.append(point)
            previous_longitude = longitude
            previous_point = point
        if len(segment) >= 3:
            segments.append(QPolygonF(segment))
        return segments

    def _draw_land(self, painter, rect):
        painter.setPen(QPen(self.LAND_BORDER_COLOR, 0.7))
        painter.setBrush(QBrush(self.LAND_COLOR))
        for ring in WORLD_LAND_POLYGONS:
            # Cheap viewport culling for the denser dataset.
            if self._view != (0.0, 0.0, 360.0, 180.0):
                lons = [point[0] for point in ring]
                lats = [point[1] for point in ring]
                try:
                    top_left = self._to_point(rect, max(lats), min(lons))
                    bottom_right = self._to_point(rect, min(lats), max(lons))
                except (TypeError, ValueError):
                    continue
                if (bottom_right.x() < rect.left() or top_left.x() > rect.right()
                        or bottom_right.y() < rect.top() or top_left.y() > rect.bottom()):
                    continue
            for polygon in self._land_segments(ring, rect):
                painter.drawPolygon(polygon)

    def _draw_borders(self, painter, rect):
        painter.setPen(QPen(QColor(120, 150, 180, 150), 0.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for line in WORLD_BORDERS:
            if self._view != (0.0, 0.0, 360.0, 180.0):
                lons = [point[0] for point in line]
                lats = [point[1] for point in line]
                try:
                    top_left = self._to_point(rect, max(lats), min(lons))
                    bottom_right = self._to_point(rect, min(lats), max(lons))
                except (TypeError, ValueError):
                    continue
                if (bottom_right.x() < rect.left() or top_left.x() > rect.right()
                        or bottom_right.y() < rect.top() or top_left.y() > rect.bottom()):
                    continue
            segment = []
            previous_longitude = None
            previous_point = None
            for longitude, latitude in line:
                point = self._to_point(rect, latitude, longitude)
                if previous_longitude is not None and (
                    abs(longitude - previous_longitude) > 180.0
                    or (previous_point is not None and abs(point.x() - previous_point.x()) > rect.width() / 2.0)
                ):
                    if len(segment) >= 2:
                        painter.drawPolyline(QPolygonF(segment))
                    segment = []
                segment.append(point)
                previous_longitude = longitude
                previous_point = point
            if len(segment) >= 2:
                painter.drawPolyline(QPolygonF(segment))

    def _draw_mountains(self, painter, rect):
        painter.setPen(QPen(QColor(150, 110, 70, 160), 0.6))
        mountain_color = QColor(150, 110, 70, 90)
        painter.setBrush(QBrush(mountain_color))
        for _name, ring in WORLD_MOUNTAINS:
            segment = []
            previous_longitude = None
            previous_point = None
            for longitude, latitude in ring:
                point = self._to_point(rect, latitude, longitude)
                if previous_longitude is not None and (
                    abs(longitude - previous_longitude) > 180.0
                    or (previous_point is not None and abs(point.x() - previous_point.x()) > rect.width() / 2.0)
                ):
                    if len(segment) >= 3:
                        painter.drawPolygon(QPolygonF(segment))
                    segment = []
                segment.append(point)
                previous_longitude = longitude
                previous_point = point
            if len(segment) >= 3:
                painter.drawPolygon(QPolygonF(segment))

    def _draw_cluster_spots(self, painter, rect):
        if not self._cluster_map_enabled:
            return
        self._prune_cluster_spots()
        for spot in self._cluster_spots:
            try:
                point = self._to_point(rect, spot["lat"], spot["lon"])
            except (TypeError, ValueError):
                continue
            if not rect.contains(point):
                continue
            color = QColor(60, 200, 120) if spot["worked"] else QColor(255, 140, 0)
            painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(point, 4.0, 4.0)

    def _draw_cities(self, painter, rect):
        center_lon, center_lat, span_lon, span_lat = self._view
        # Population thresholds by zoom level.
        if span_lon >= 120.0:
            min_population = 7_000_000
        elif span_lon >= 40.0:
            min_population = 100_000
        elif span_lon >= 10.0:
            min_population = 40_000
        else:
            min_population = 0

        # Focus the detailed city set around the correspondent when one is
        # known; otherwise fall back to the whole visible area.
        focus_lat = None
        focus_lon = None
        focus_radius_km = None
        if self.station_locator:
            try:
                focus_lat, focus_lon = locator_to_latlon(self.station_locator)
            except (TypeError, ValueError):
                focus_lat = focus_lon = None
        if focus_lat is not None:
            # The visible area grows as we zoom out, so the focused city
            # cluster grows with it.
            focus_radius_km = min(2500.0, max(120.0, span_lon * 111.0 * 0.45))

        font = QFont("Sans", 7)
        painter.setFont(font)
        for name, lon, lat, pop, capital in WORLD_CITIES:
            if pop < min_population and not capital:
                continue
            if capital and pop < min_population and span_lon >= 120.0:
                # Keep only reasonably large capitals on the world view.
                if pop < 7_000_000:
                    continue
            if focus_lat is not None and focus_radius_km is not None:
                try:
                    dist = distance_km(focus_lat, focus_lon, lat, lon)
                except (TypeError, ValueError):
                    dist = 0.0
                if dist > focus_radius_km:
                    continue
            try:
                point = self._to_point(rect, lat, lon)
            except (TypeError, ValueError):
                continue
            if not rect.contains(point):
                continue
            color = QColor(255, 210, 90) if capital else QColor(220, 220, 220)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(point, 2.0 if capital else 1.2, 2.0 if capital else 1.2)
            if capital or span_lon < 40.0:
                painter.setPen(QPen(self.TEXT_COLOR))
                painter.drawText(
                    QRectF(point.x() + 4.0, point.y() - 8.0, 80.0, 12.0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    name,
                )

    def _draw_grid(self, painter, rect):
        cell_width = rect.width() / 18.0
        cell_height = rect.height() / 18.0
        painter.setPen(QPen(self.GRID_COLOR, 0.7))
        for index in range(1, 18):
            x = rect.left() + index * cell_width
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            y = rect.top() + index * cell_height
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        painter.setPen(QPen(self.GRID_COLOR, 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        font = QFont("Sans", 6)
        painter.setFont(font)
        painter.setPen(QPen(self.GRID_LABEL_COLOR))
        for index in range(18):
            letter = chr(ord("A") + index)
            x = rect.left() + (index + 0.5) * cell_width
            painter.drawText(
                QRectF(x - 8.0, rect.top() - 14.0, 16.0, 11.0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                letter,
            )
            y = rect.bottom() - (index + 0.5) * cell_height
            painter.drawText(
                QRectF(rect.left() - 21.0, y - 6.0, 17.0, 12.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                letter,
            )

    @staticmethod
    def _locator_cell_rect(rect, locator, level=1):
        loc = normalize_locator(locator)
        if not loc:
            return QRectF()
        cell_width = rect.width() / 18.0
        cell_height = rect.height() / 18.0
        lon_field = ord(loc[0]) - ord("A")
        lat_field = ord(loc[1]) - ord("A")
        left = rect.left() + lon_field * cell_width
        top = rect.top() + (17 - lat_field) * cell_height
        width = cell_width
        height = cell_height
        if level >= 2 and len(loc) >= 4:
            width = cell_width / 10.0
            height = cell_height / 10.0
            left += int(loc[2]) * width
            top += (9 - int(loc[3])) * height
        return QRectF(left, top, width, height)

    def _draw_locator_highlight(self, painter, rect, locator, color):
        field_rect = self._locator_cell_rect(rect, locator, level=1)
        if field_rect.isEmpty():
            return
        field_color = QColor(color)
        field_color.setAlpha(42)
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 110), 0.8))
        painter.setBrush(QBrush(field_color))
        painter.drawRect(field_rect)

        square_rect = self._locator_cell_rect(rect, locator, level=2)
        if square_rect.isEmpty() or square_rect == field_rect:
            return
        square_color = QColor(color)
        square_color.setAlpha(95)
        painter.setPen(QPen(color, 1.0))
        painter.setBrush(QBrush(square_color))
        painter.drawRect(square_rect)

    def _draw_line(self, painter, rect, my_point, station_point):
        if my_point is None or station_point is None:
            return
        try:
            my_lat, my_lon = locator_to_latlon(self.my_locator)
            station_lat, station_lon = locator_to_latlon(self.station_locator)
        except ValueError:
            return
        path = great_circle_points(my_lat, my_lon, station_lat, station_lon)
        painter.setPen(QPen(self.LINE_COLOR, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        segment = []
        previous_longitude = None
        for latitude, longitude in path:
            if previous_longitude is not None and abs(longitude - previous_longitude) > 180.0:
                if len(segment) >= 2:
                    painter.drawPolyline(QPolygonF(segment))
                segment = []
            segment.append(self._to_point(rect, latitude, longitude))
            previous_longitude = longitude
        if len(segment) >= 2:
            painter.drawPolyline(QPolygonF(segment))

    def _draw_marker(self, painter, rect, point, color, label):
        if point is None:
            return
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(point, 5.5, 5.5)

        font = QFont("Sans", 7)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(label) + 10.0
        height = 16.0
        box = QRectF(point.x() + 8.0, point.y() - height - 5.0, width, height)
        if box.right() > rect.right():
            box.moveLeft(point.x() - width - 8.0)
        if box.top() < rect.top():
            box.moveTop(point.y() + 8.0)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor(9, 20, 31, 215)))
        painter.drawRoundedRect(box, 3.0, 3.0)
        painter.setPen(QPen(self.TEXT_COLOR))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, label)

    @staticmethod
    def _format_distance(value):
        return f"{value:,.0f}".replace(",", " ")

    def _distance_text(self):
        if not self.my_locator:
            return "Set your QTH locator in Menu -> Settings"
        if not self.station_call:
            return "Enter a callsign to show the distance"
        if not self.station_locator:
            return f"Locator for {self.station_call} was not found"
        try:
            my_lat, my_lon = locator_to_latlon(self.my_locator)
            station_lat, station_lon = locator_to_latlon(self.station_locator)
        except ValueError:
            return "Invalid locator"
        distance = distance_km(my_lat, my_lon, station_lat, station_lon)
        bearing = bearing_deg(my_lat, my_lon, station_lat, station_lon)
        return (
            f"{self.station_call}: {self._format_distance(distance)} km   "
            f"azimuth {bearing:.0f} deg"
        )

    def _draw_info(self, painter, rect):
        text = self._distance_text()
        font = QFont("Sans", 9)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width = min(rect.width() - 16.0, metrics.horizontalAdvance(text) + 18.0)
        box = QRectF(rect.left() + 8.0, rect.top() + 8.0, width, 24.0)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor(8, 18, 29, 205)))
        painter.drawRoundedRect(box, 4.0, 4.0)
        painter.setPen(QPen(self.TEXT_COLOR))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self.OCEAN_COLOR)

        rect = self._map_rect()
        if rect.isEmpty():
            painter.end()
            return

        self._update_view(rect)

        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(self.OCEAN_COLOR))
        painter.drawRect(rect)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        self._draw_land(painter, rect)
        self._draw_borders(painter, rect)
        self._draw_mountains(painter, rect)
        self._draw_cities(painter, rect)
        self._draw_cluster_spots(painter, rect)
        if self._view == (0.0, 0.0, 360.0, 180.0):
            self._draw_grid(painter, rect)
        if self._view == (0.0, 0.0, 360.0, 180.0):
            self._draw_locator_highlight(painter, rect, self.my_locator, self.MY_COLOR)
            self._draw_locator_highlight(
                painter, rect, self.station_locator, self.STATION_COLOR
            )

        my_point = None
        station_point = None
        if self.my_locator:
            try:
                my_lat, my_lon = locator_to_latlon(self.my_locator)
                my_point = self._to_point(rect, my_lat, my_lon)
            except ValueError:
                my_point = None
        if self.station_locator:
            try:
                station_lat, station_lon = locator_to_latlon(self.station_locator)
                station_point = self._to_point(rect, station_lat, station_lon)
            except ValueError:
                station_point = None

        self._draw_line(painter, rect, my_point, station_point)
        self._draw_marker(painter, rect, my_point, self.MY_COLOR, f"MY {self.my_locator}")
        if station_point is not None:
            self._draw_marker(
                painter,
                rect,
                station_point,
                self.STATION_COLOR,
                f"{self.station_call} {self.station_locator}".strip(),
            )
        self._draw_info(painter, rect)
        painter.end()


class QTHMapWindow(QWidget):
    """Separate window hosting the QTH map and a short status line."""

    def __init__(self, settings_dict, parent=None):
        super().__init__(parent)
        self.settings_dict = settings_dict
        self._preserve_visibility_on_close = False
        self.flag_button = None
        self.offset = None
        self.resize_wnd = None
        self._resize_origin_size = None
        self.setWindowTitle("QTH map")
        if settings_dict.get("border_wnd") == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        try:
            left = int(settings_dict.get("qth-map-window-left", ""))
            top = int(settings_dict.get("qth-map-window-top", ""))
            width = int(settings_dict.get("qth-map-window-width", ""))
            height = int(settings_dict.get("qth-map-window-height", ""))
            if width > 0 and height > 0:
                self.setGeometry(left, top, width, height)
            else:
                self.resize(900, 520)
        except (TypeError, ValueError):
            self.resize(900, 520)
        self.setMinimumSize(640, 400)
        style = (
            "background-color:" + settings_dict.get("background-color", "#08131f")
            + "; color:" + settings_dict.get("color", "#c0bfbc") + ";"
        )
        self.setStyleSheet(style)

        self.map = QTHMapWidget(settings_dict, self)
        self.zoom_in_button = QPushButton("+", self)
        self.zoom_out_button = QPushButton("-", self)
        for button in (self.zoom_in_button, self.zoom_out_button):
            button.setFixedSize(28, 28)
            button.setStyleSheet(
                "QPushButton { background-color: rgba(0, 0, 0, 120); color: white; "
                "border: 2px solid rgba(255, 255, 255, 180); border-radius: 0px; "
                "font: bold 14px; }"
            )
        self.zoom_in_button.clicked.connect(self.map.zoom_in)
        self.zoom_out_button.clicked.connect(self.map.zoom_out)
        self.cluster_map_button = QPushButton("Cluster Map", self)
        self.cluster_map_button.setFixedHeight(28)
        self.cluster_map_button.setFixedWidth(96)
        self.cluster_map_button.setStyleSheet(
            "QPushButton { background-color: rgba(0, 0, 0, 120); color: white; "
            "border: 2px solid rgba(255, 255, 255, 180); border-radius: 0px; "
            "font: bold 11px; }"
        )
        self.cluster_map_button.clicked.connect(self._toggle_cluster_map)
        self.info = QLabel(self)

    def _toggle_cluster_map(self):
        enabled = not self.map._cluster_map_enabled
        self.map.set_cluster_map_enabled(enabled)
        self.cluster_map_button.setText("Cluster Map" if not enabled else "Hide Cluster")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("font: 9pt; padding: 2px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addWidget(self.map, 1)
        layout.addWidget(self.info)
        self.refresh_my_locator()

    def refresh_my_locator(self):
        self.map.set_my_locator(self.settings_dict.get("my-qth-locator", ""))
        self._update_info()

    def set_station(self, call, locator, source=""):
        self.map.set_station(call, locator, source)
        self._update_info()

    def clear_station(self):
        self.map.clear_station()
        self._update_info()

    def _update_info(self):
        parts = ["My locator: " + (self.map.my_locator or "not set")]
        if self.map.station_call:
            if self.map.station_locator:
                value = f"{self.map.station_call}: {self.map.station_locator}"
                if self.map.station_source:
                    value += f" ({self.map.station_source})"
                parts.append(value)
            else:
                parts.append(f"{self.map.station_call}: locator not found")
        self.info.setText("   |   ".join(parts))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        map_rect = self.map._map_rect()
        if map_rect.isEmpty():
            right = self.width() - 8
            bottom = self.height() - 8
        else:
            right = int(self.map.x() + map_rect.right())
            bottom = int(self.map.y() + map_rect.bottom())
        self.zoom_out_button.move(right - 32, bottom - 32)
        self.zoom_in_button.move(right - 32, bottom - 66)
        self.cluster_map_button.move(right - 132, bottom - 32)
        self.zoom_in_button.raise_()
        self.zoom_out_button.raise_()

    def closeEvent(self, event):
        try:
            geometry = self.geometry()
            self.settings_dict["qth-map-window-left"] = str(geometry.left())
            self.settings_dict["qth-map-window-top"] = str(geometry.top())
            self.settings_dict["qth-map-window-width"] = str(geometry.width())
            self.settings_dict["qth-map-window-height"] = str(geometry.height())
            if not getattr(self, "_preserve_visibility_on_close", False):
                self.settings_dict["qth-map-window"] = "False"
        except Exception:
            pass
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self._resize_origin_size = (self.width(), self.height())
            self.flag_button = "right"
        elif event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"

    def mouseMoveEvent(self, event):
        if self.flag_button == "left" and self.offset is not None:
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            self.move(x - self.offset.x(), y - self.offset.y())
        elif self.flag_button == "right" and self.resize_wnd is not None and self._resize_origin_size is not None:
            delta_x = self.resize_wnd.x() - event.pos().x()
            delta_y = self.resize_wnd.y() - event.pos().y()
            width = max(self.minimumWidth(), self._resize_origin_size[0] - delta_x)
            height = max(self.minimumHeight(), self._resize_origin_size[1] - delta_y)
            self.resize(width, height)

    def mouseReleaseEvent(self, event):
        self.flag_button = None
        self.offset = None
        self.resize_wnd = None
        self._resize_origin_size = None
