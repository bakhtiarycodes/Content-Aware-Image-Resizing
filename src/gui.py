# src/gui.py
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QFileDialog, QSlider, QHBoxLayout, QSpinBox, QFrame,
    QProgressBar, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt
from src.seam_carving import seam_carve
from src.styles import QSS
from PyQt5.QtCore import QTimer, QElapsedTimer  # add to imports


class SeamCarvingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Resizing GUI (Nankai University)")
        self.image = None
        self.resized = None
        self.is_expanding = False
        self.setWindowIcon(QIcon("Image/Icon/cubic.png"))
        self.setStyleSheet(QSS)  # dark them

        self.elapsed_timer = QElapsedTimer()  # stop-watch
        self.display_timer = QTimer()  # 50 ms refresh
        self.display_timer.timeout.connect(self._update_time_label)

        # --------------------  widgets  --------------------
        shadow = QGraphicsDropShadowEffect(blurRadius=12, xOffset=2, yOffset=2, color=Qt.black)
        shadow1 = QGraphicsDropShadowEffect(blurRadius=12, xOffset=2, yOffset=2, color=Qt.black)
        self.original_label = QLabel()
        self.resized_label = QLabel()
        self.original_dim = QLabel("Original:  - × -")
        self.original_size = QLabel("Size:  - KB")
        self.resized_dim = QLabel("Resized:  - × -")
        self.resized_size = QLabel("Size:  - KB")
        for lbl in (self.original_dim, self.original_size, self.resized_dim, self.resized_size):
            lbl.setAlignment(Qt.AlignCenter)
        self.original_label.setFixedSize(1800, 1400)
        self.original_label.setGraphicsEffect(shadow1)
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setScaledContents(False)

        self.resized_label.setFixedSize(1800, 1400)
        self.resized_label.setGraphicsEffect(shadow)
        self.resized_label.setAlignment(Qt.AlignCenter)
        self.resized_label.setScaledContents(False)

        self.load_button = QPushButton("  📂  Load Image")
        self.carve_button = QPushButton("  ⚙️  Run Seam Carving")
        self.save_button = QPushButton("  💾  Save Resized Image")
        self.expand_button = QPushButton("  ➕  Expand Image (Shrink)")
        for btn in (self.carve_button, self.expand_button, self.save_button):
            btn.setEnabled(False)

        # sliders / spin-boxes
        self.width_slider = QSlider(Qt.Horizontal);
        self.width_slider.setValue(70)
        self.height_slider = QSlider(Qt.Horizontal);
        self.height_slider.setValue(70)
        self.width_spinbox = QSpinBox();
        self.width_spinbox.setValue(70);
        self.width_spinbox.setSuffix(" %")
        self.height_spinbox = QSpinBox();
        self.height_spinbox.setValue(70);
        self.height_spinbox.setSuffix(" %")
        self.width_pixel2keep = QSpinBox();
        self.width_pixel2keep.setSuffix(" px")
        self.height_pixel2keep = QSpinBox();
        self.height_pixel2keep.setSuffix(" px")

        # progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)

        # ----------  elapsed-time row  ----------
        self.time_label = QLabel("Elapsed:  0.00 s")
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Time  "))
        time_row.addWidget(self.time_label)
        time_row.addStretch()
        time_row.setContentsMargins(0, 0, 0, 0)  # no outer padding
        time_row.setSpacing(3)  # tighter gap
        self.time_label.setObjectName("time_label")

        # --------------------  expansion-aware sync  --------------------
        def _update_ranges():
            """switch min/max depending on mode"""
            if self.image is None: return
            h, w = self.image.shape[:2]
            if self.is_expanding:  # 100-200 % ,  w-2w px
                self.width_slider.setRange(100, 200);
                self.width_spinbox.setRange(100, 200)
                self.height_slider.setRange(100, 200);
                self.height_spinbox.setRange(100, 200)
                self.width_pixel2keep.setRange(w, 2 * w);
                self.height_pixel2keep.setRange(h, 2 * h)
            else:  # 10-100 % ,  0.1w-w px
                self.width_slider.setRange(10, 100);
                self.width_spinbox.setRange(10, 100)
                self.height_slider.setRange(10, 100);
                self.height_spinbox.setRange(10, 100)
                self.width_pixel2keep.setRange(int(0.1 * w), w);
                self.height_pixel2keep.setRange(int(0.1 * h), h)

        def _sync_pixels_to_sliders():
            """keep pixel spin consistent with % slider"""
            if self.image is None: return
            h, w = self.image.shape[:2]
            if self.is_expanding:
                extra_w = int((self.width_slider.value() - 100) / 100 * w)
                extra_h = int((self.height_slider.value() - 100) / 100 * h)
                self.width_pixel2keep.setValue(w + extra_w)
                self.height_pixel2keep.setValue(h + extra_h)
            else:
                self.width_pixel2keep.setValue(int(self.width_slider.value() / 100 * w))
                self.height_pixel2keep.setValue(int(self.height_slider.value() / 100 * h))

        # old plain sync (only % widgets)
        def sync_w_slider(val):
            self.width_spinbox.setValue(val)

        def sync_w_spin(val):
            self.width_slider.setValue(val)

        def sync_h_slider(val):
            self.height_spinbox.setValue(val)

        def sync_h_spin(val):
            self.height_slider.setValue(val)

        # wrapped versions that also update pixel box
        def new_w_slider(val):
            sync_w_slider(val);  _sync_pixels_to_sliders()

        def new_h_slider(val):
            sync_h_slider(val);  _sync_pixels_to_sliders()

        # --------------------  connections  --------------------
        self.width_slider.valueChanged.connect(new_w_slider)
        self.height_slider.valueChanged.connect(new_h_slider)
        self.width_spinbox.valueChanged.connect(sync_w_spin)
        self.height_spinbox.valueChanged.connect(sync_h_spin)

        #  NEW 1  –  connect pixel boxes back to percentage controls
        self.width_pixel2keep.valueChanged.connect(self._sync_percentage_to_pixels)
        self.height_pixel2keep.valueChanged.connect(self._sync_percentage_to_pixels)

        def toggle_mode():
            self.is_expanding = not self.is_expanding
            self.expand_button.setText("  ➖  Shrink Image" if self.is_expanding else "  ➕  Expand Image")
            # ----------  auto-toggle mode  ----------
            self.carve_button.setText(
                "  ⚙️  Run Seam Carving (Expand)" if self.is_expanding else "  ⚙️  Run Seam Carving (Shrink)")
            _update_ranges()
            _sync_pixels_to_sliders()

        self.expand_button.clicked.connect(toggle_mode)

        # --------------------  layouts  --------------------
        original_frame = QFrame();
        original_frame.setFrameShape(QFrame.Panel);
        original_frame.setLineWidth(0)
        resized_frame = QFrame();
        resized_frame.setFrameShape(QFrame.Panel);
        resized_frame.setLineWidth(0)

        orig_v = QVBoxLayout();
        orig_v.addWidget(self.original_label);
        orig_v.addWidget(self.original_dim);
        orig_v.addWidget(self.original_size)
        original_frame.setLayout(orig_v)
        res_v = QVBoxLayout();
        res_v.addWidget(self.resized_label);
        res_v.addWidget(self.resized_dim);
        res_v.addWidget(self.resized_size)
        resized_frame.setLayout(res_v)

        mid = QHBoxLayout();
        mid.addWidget(original_frame);
        mid.addWidget(resized_frame)

        progress_h = QHBoxLayout();
        progress_h.addWidget(QLabel("Progress"));
        progress_h.addWidget(self.progress_bar)

        width_h = QHBoxLayout();
        width_h.addWidget(QLabel("Width "));
        width_h.addWidget(self.width_slider);
        width_h.addWidget(self.width_spinbox);
        width_h.addWidget(self.width_pixel2keep)
        height_h = QHBoxLayout();
        height_h.addWidget(QLabel("Height"));
        height_h.addWidget(self.height_slider);
        height_h.addWidget(self.height_spinbox);
        height_h.addWidget(self.height_pixel2keep)

        button_h = QHBoxLayout()
        button_h.addWidget(self.load_button);
        button_h.addWidget(self.carve_button)
        button_h.addWidget(self.expand_button);
        button_h.addWidget(self.save_button)

        main_v = QVBoxLayout()
        main_v.addLayout(mid)
        main_v.addLayout(progress_h)
        main_v.addLayout(time_row)
        main_v.addLayout(height_h)
        main_v.addLayout(width_h)
        main_v.addLayout(button_h)
        main_v.addSpacing(40)
        self.setLayout(main_v)
        self.showMaximized()

        # --------------------  functional connections  --------------------
        self.load_button.clicked.connect(self.load_image)
        self.carve_button.clicked.connect(self.run_carving)
        self.save_button.clicked.connect(self.save_image)

    # --------------------  slots  --------------------
    def cv_to_pixmap(self, cv_img):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def load_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.jpg *.png *.jpeg)")
        if fname:
            self.image = cv2.imread(fname)
            size_kb = round(self.image.nbytes / 1024, 2)
            h, w = self.image.shape[:2]
            self.original_dim.setText(f"Original:  {w} × {h}")
            self.original_size.setText(f"Size:  {size_kb} KB")
            self.original_label.setPixmap(self.cv_to_pixmap(self.image).scaled(2000, 1300, Qt.KeepAspectRatio))

            # set correct ranges + initialise pixel box
            self._update_ranges()
            self._sync_pixels_to_sliders()
            for btn in (self.carve_button, self.expand_button):
                btn.setEnabled(True)

    # wrappers so they can be called from inside __init__
    def _update_ranges(self):
        if self.image is None: return
        h, w = self.image.shape[:2]
        if self.is_expanding:
            self.width_slider.setRange(100, 200);
            self.width_spinbox.setRange(100, 200)
            self.height_slider.setRange(100, 200);
            self.height_spinbox.setRange(100, 200)
            self.width_pixel2keep.setRange(w, 2 * w);
            self.height_pixel2keep.setRange(h, 2 * h)
        else:
            self.width_slider.setRange(10, 100);
            self.width_spinbox.setRange(10, 100)
            self.height_slider.setRange(10, 100);
            self.height_spinbox.setRange(10, 100)
            self.width_pixel2keep.setRange(int(0.1 * w), w);
            self.height_pixel2keep.setRange(int(0.1 * h), h)

    def _sync_pixels_to_sliders(self):
        if self.image is None: return

        # Block signals to prevent recursive updates
        self.width_pixel2keep.blockSignals(True)
        self.height_pixel2keep.blockSignals(True)

        h, w = self.image.shape[:2]
        if self.is_expanding:
            extra_w = int((self.width_slider.value() - 100) / 100 * w)
            extra_h = int((self.height_slider.value() - 100) / 100 * h)
            self.width_pixel2keep.setValue(w + extra_w)
            self.height_pixel2keep.setValue(h + extra_h)
        else:
            self.width_pixel2keep.setValue(int(self.width_slider.value() / 100 * w))
            self.height_pixel2keep.setValue(int(self.height_slider.value() / 100 * h))

        # Unblock signals
        self.width_pixel2keep.blockSignals(False)
        self.height_pixel2keep.blockSignals(False)

    #   reverse sync (pixel -> %)
    def _sync_percentage_to_pixels(self):
        """User typed a pixel count  ->  update % slider/spinbox."""
        if self.image is None:
            return

        # Block signals to prevent recursive updates
        self.width_pixel2keep.blockSignals(True)
        self.height_pixel2keep.blockSignals(True)

        h, w = self.image.shape[:2]

        # width
        target_px = self.width_pixel2keep.value()
        if self.is_expanding:
            pct = 100 + int(round((target_px - w) / w * 100))
        else:
            pct = int(round(target_px / w * 100))
        pct = max(self.width_slider.minimum(),
                  min(self.width_slider.maximum(), pct))
        self.width_slider.setValue(pct)  # will auto-update % spinbox

        # height
        target_px = self.height_pixel2keep.value()
        if self.is_expanding:
            pct = 100 + int(round((target_px - h) / h * 100))
        else:
            pct = int(round(target_px / h * 100))
        pct = max(self.height_slider.minimum(),
                  min(self.height_slider.maximum(), pct))
        self.height_slider.setValue(pct)

        # Unblock signals
        self.width_pixel2keep.blockSignals(False)
        self.height_pixel2keep.blockSignals(False)

    def run_carving(self):
        if self.image is None:
            return
        if self.image is None: return
        w_pct = self.width_spinbox.value()
        h_pct = self.height_spinbox.value()
        target_w = int(self.image.shape[1] * w_pct / 100)
        target_h = int(self.image.shape[0] * h_pct / 100)
        v_seams = abs(self.image.shape[1] - target_w)
        h_seams = abs(self.image.shape[0] - target_h)

        total = (2 * (v_seams + h_seams)) if self.is_expanding else (v_seams + h_seams)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)

        # ----------  start stop-watch  ----------
        self.elapsed_timer.start()
        self.display_timer.start(50)  # update label every 50 ms

        step = 0

        def progress(curr, direction, phase=None):
            nonlocal step
            if self.is_expanding:
                txt = f"{direction}  –  {phase}ing …"
                self.progress_bar.setFormat(txt)
                step += 1
            else:
                txt = f"{direction}  –  removing …"
                self.progress_bar.setFormat(txt)
                step = curr if direction == "Vertical" else v_seams + curr
            self.progress_bar.setValue(step)
            QApplication.processEvents()

        carved = seam_carve(self.image.copy(), v_seams, h_seams,
                            progress_callback=progress, expand=self.is_expanding)
        self.resized = carved
        self.save_button.setEnabled(True)
        self.progress_bar.setFormat("Finished")
        size_kb = round(carved.nbytes / 1024, 2)
        h, w = carved.shape[:2]
        self.resized_dim.setText(f"Resized:  {w} × {h}")
        self.resized_size.setText(f"Size:  {size_kb} KB")
        self.resized_label.setPixmap(self.cv_to_pixmap(carved).scaled(2000, 1300, Qt.KeepAspectRatio))

        self.display_timer.stop()
        self._update_time_label()  # final precise value

    def _update_time_label(self):
        ms = self.elapsed_timer.elapsed()
        min = ms // 60000
        sec = (ms % 60000) / 1000
        self.time_label.setText(f"Elapsed:  {min:02.0f}:{sec:05.2f}")

    def save_image(self):
        if self.resized is not None:
            fname, _ = QFileDialog.getSaveFileName(self, "Save Image", "resized_output.jpg",
                                                   "Images (*.jpg *.png)")
            if fname:
                cv2.imwrite(fname, self.resized)