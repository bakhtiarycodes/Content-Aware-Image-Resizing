# src/styles.py
QSS = """
/* ----------  global palette  ---------- */
QWidget {
    background: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", Ubuntu, sans-serif;
    font-size: 10pt;
}

/* ----------  buttons  ---------- */
QPushButton {
    background: #3c3c3c;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 80px;
    min-height: 40px;
    font-size: 30px;
}
QPushButton:hover {
    background: #4a4a4a;
    border: 1px solid #6a6a6a;
}
QPushButton:pressed {
    background: #262626;
    border: 1px solid #3c3c3c;
}
QPushButton:disabled {
    background: #353535;
    border: 1px solid #454545;
    color: #888;
}

/* ----------  sliders  ---------- */
QSlider::groove:horizontal {
    height: 6px;
    background: #3c3c3c;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #606060;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #808080;
}

/* ----------  spin-boxes  ---------- */
QSpinBox {
    background: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
    width: 150px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #505050;
    border-radius: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #707070;
}

/* ----------  frames  ---------- */
QFrame[frameShape="4"] {
    border: 1px solid #555;
    border-radius: 6px;
    padding: 4px;
}

/* ----------  progress-bar  ---------- */
QProgressBar {
    background: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a, stop:1 #6bb);
    border-radius: 3px;
}
/* ----------  compact timer  ---------- */
QLabel#time_label {          /* we must set the object-name in code */
    font-size: 9pt;
    min-height: 40px;
    max-height: 40px;
    padding: 0px;
}
"""