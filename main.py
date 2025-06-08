import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QSlider, QToolBar, QAction, QProgressBar, QColorDialog
)
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint


class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sleek Image Processing App")
        self.setGeometry(100, 100, 1000, 700)

        # Core state variables
        self.image = None
        self.processed_image = None
        self.image_history = []
        self.drawing = False
        self.brush_color = QColor(Qt.red)
        self.brush_size = 5
        self.last_point = QPoint()
        self.theme_dark = True
        self.live_preview = False

        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.label = QLabel()
        self.label.setMinimumSize(640, 480)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("border: 1px solid gray; background-color: #222;")

        # Layouts
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        control_layout = QVBoxLayout()

        layout.addWidget(self.label)
        layout.addLayout(btn_layout)
        layout.addLayout(control_layout)

        # Buttons
        def create_button(text, func):
            btn = QPushButton(text)
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)
            return btn

        create_button("Open Image", self.open_image)
        create_button("Save Image", self.save_image)
        create_button("Reset", self.reset_image)
        create_button("Grayscale", self.apply_grayscale)
        create_button("Gaussian Blur", self.apply_blur)
        create_button("Edge Detection", self.apply_edge_detection)
        create_button("Start Live Preview", self.start_camera)
        create_button("Stop Preview", self.stop_camera)
        create_button("Pick Color", self.pick_color)

        # Sliders
        self.blur_slider = self.create_slider(1, 21, 5, control_layout, "Blur Intensity", self.apply_blur, step=2)
        self.brightness_slider = self.create_slider(-100, 100, 0, control_layout, "Brightness", self.adjust_brightness_contrast)
        self.contrast_slider = self.create_slider(-100, 100, 0, control_layout, "Contrast", self.adjust_brightness_contrast)
        self.brush_slider = self.create_slider(1, 30, 5, control_layout, "Brush Size", self.update_brush_size)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        control_layout.addWidget(self.progress_bar)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo_action)
        toolbar.addAction(undo_action)

        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

        central_widget.setLayout(layout)
        self.setAcceptDrops(True)

    def create_slider(self, min_val, max_val, init, parent_layout, label_text, callback, step=1):
        from PyQt5.QtWidgets import QLabel
        parent_layout.addWidget(QLabel(label_text))
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(init)
        slider.setSingleStep(step)
        slider.valueChanged.connect(callback)
        parent_layout.addWidget(slider)
        return slider

    # File handling
    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            self.image = cv2.imread(file_name)
            self.processed_image = self.image.copy()
            self.image_history.clear()
            self.display_image(self.image)

    def save_image(self):
        if self.processed_image is not None:
            self.progress_bar.setValue(0)
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png)")
            if file_name:
                self.progress_bar.setValue(25)
                cv2.imwrite(file_name, self.processed_image)
                self.progress_bar.setValue(100)

    def reset_image(self):
        if self.image is not None:
            self.processed_image = self.image.copy()
            self.display_image(self.image)

    # Image display
    def display_image(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))

    # Image Processing
    def apply_grayscale(self):
        if self.processed_image is not None:
            self.image_history.append(self.processed_image.copy())
            gray = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2GRAY)
            self.processed_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            self.display_image(self.processed_image)

    def apply_blur(self):
        if self.processed_image is not None:
            self.image_history.append(self.processed_image.copy())
            k = self.blur_slider.value()
            k = k if k % 2 == 1 else k + 1
            blurred = cv2.GaussianBlur(self.processed_image, (k, k), 0)
            self.processed_image = blurred
            self.display_image(self.processed_image)

    def apply_edge_detection(self):
        if self.processed_image is not None:
            self.image_history.append(self.processed_image.copy())
            gray = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            self.processed_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            self.display_image(self.processed_image)

    def adjust_brightness_contrast(self):
        if self.image is not None:
            self.image_history.append(self.processed_image.copy())
            brightness = self.brightness_slider.value()
            contrast = self.contrast_slider.value()
            img = np.int16(self.image)
            img = img * (contrast / 100 + 1) - contrast + brightness
            img = np.clip(img, 0, 255)
            self.processed_image = np.uint8(img)
            self.display_image(self.processed_image)

    def undo_action(self):
        if self.image_history:
            self.processed_image = self.image_history.pop()
            self.display_image(self.processed_image)

    def toggle_theme(self):
        if self.theme_dark:
            self.setStyleSheet("background-color: #f0f0f0; color: black;")
            self.label.setStyleSheet("border: 1px solid gray; background-color: white;")
        else:
            self.setStyleSheet("background-color: #2e2e2e; color: white;")
            self.label.setStyleSheet("border: 1px solid gray; background-color: #222;")
        self.theme_dark = not self.theme_dark

    # Drawing with mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.processed_image is not None:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and self.processed_image is not None and self.label.pixmap():
            label_pos = self.label.mapToGlobal(QPoint(0, 0))
            x_scale = self.processed_image.shape[1] / self.label.width()
            y_scale = self.processed_image.shape[0] / self.label.height()

            x1 = int((self.last_point.x() - self.label.pos().x()) * x_scale)
            y1 = int((self.last_point.y() - self.label.pos().y()) * y_scale)
            x2 = int((event.x() - self.label.pos().x()) * x_scale)
            y2 = int((event.y() - self.label.pos().y()) * y_scale)

            cv2.line(self.processed_image, (x1, y1), (x2, y2),
                     (self.brush_color.red(), self.brush_color.green(), self.brush_color.blue()), self.brush_size)
            self.display_image(self.processed_image)
            self.last_point = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = color

    def update_brush_size(self, value):
        self.brush_size = value

    # Drag and Drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.image = cv2.imread(file_path)
            self.processed_image = self.image.copy()
            self.image_history.clear()
            self.display_image(self.image)

    # Live camera
    def start_camera(self):
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.live_preview = True

    def stop_camera(self):
        if hasattr(self, 'capture'):
            self.timer.stop()
            self.capture.release()
            self.live_preview = False

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            self.processed_image = frame.copy()
            self.display_image(frame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec_())
