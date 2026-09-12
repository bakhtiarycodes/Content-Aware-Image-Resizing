# src/seam_carving.py
import cv2
import numpy as np
import time
from PyQt5.QtWidgets import QApplication   # for processEvents


# ------------------------------------------------------------------
#  ENERGY
# ------------------------------------------------------------------
def compute_energy(image):
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1)
    return np.abs(sobel_x) + np.abs(sobel_y)


# ------------------------------------------------------------------
#  SEAM FINDERS
# ------------------------------------------------------------------
def find_vertical_seam(energy):
    rows, cols = energy.shape
    cost = energy.copy()
    backtrack = np.zeros_like(cost, dtype=int)

    for i in range(1, rows):
        for j in range(cols):
            min_val = cost[i - 1, j]
            idx = j
            if j > 0 and cost[i - 1, j - 1] < min_val:
                min_val = cost[i - 1, j - 1]
                idx = j - 1
            if j < cols - 1 and cost[i - 1, j + 1] < min_val:
                min_val = cost[i - 1, j + 1]
                idx = j + 1
            cost[i, j] += min_val
            backtrack[i, j] = idx

    seam = np.zeros(rows, dtype=int)
    seam[-1] = np.argmin(cost[-1])
    for i in range(rows - 2, -1, -1):
        seam[i] = backtrack[i + 1, seam[i + 1]]
    return seam


def find_horizontal_seam(energy):
    rows, cols = energy.shape
    cost = energy.copy()
    backtrack = np.zeros_like(cost, dtype=int)

    for j in range(1, cols):
        for i in range(rows):
            min_val = cost[i, j - 1]
            idx = i
            if i > 0 and cost[i - 1, j - 1] < min_val:
                min_val = cost[i - 1, j - 1]
                idx = i - 1
            if i < rows - 1 and cost[i + 1, j - 1] < min_val:
                min_val = cost[i + 1, j - 1]
                idx = i + 1
            cost[i, j] += min_val
            backtrack[i, j] = idx

    seam = np.zeros(cols, dtype=int)
    seam[-1] = np.argmin(cost[:, -1])
    for j in range(cols - 2, -1, -1):
        seam[j] = backtrack[seam[j + 1], j + 1]
    return seam


# ------------------------------------------------------------------
#  REMOVE SEAMS  (shrinking)
# ------------------------------------------------------------------
def remove_vertical_seam(image, seam):
    rows, cols, _ = image.shape
    out = np.zeros((rows, cols - 1, 3), dtype=np.uint8)
    for i in range(rows):
        out[i] = np.delete(image[i], seam[i], axis=0)
    return out


def remove_horizontal_seam(image, seam):
    rows, cols, _ = image.shape
    out = np.zeros((rows - 1, cols, 3), dtype=np.uint8)
    for j in range(cols):
        out[:, j] = np.delete(image[:, j], seam[j], axis=0)
    return out


# ------------------------------------------------------------------
#  INSERT SEAMS  (expansion)
# ------------------------------------------------------------------
def insert_vertical_seam(img, seams):
    h, w, c = img.shape
    k = len(seams)
    out = np.zeros((h, w + k, c), dtype=img.dtype)
    for i in range(h):
        seam_positions = sorted([s[i] for s in seams])
        offset = 0
        for j in range(w):
            out[i, j + offset] = img[i, j]
            if j in seam_positions:
                out[i, j + offset + 1] = img[i, j]  # duplicate
                offset += 1
    return out


def insert_horizontal_seam(img, seams):
    h, w, c = img.shape
    k = len(seams)
    out = np.zeros((h + k, w, c), dtype=img.dtype)
    for j in range(w):
        seam_positions = sorted([s[j] for s in seams])
        offset = 0
        for i in range(h):
            out[i + offset, j] = img[i, j]
            if i in seam_positions:
                out[i + offset + 1, j] = img[i, j]
                offset += 1
    return out


# ------------------------------------------------------------------
#  MAIN DRIVER
# ------------------------------------------------------------------
def seam_carve(image, num_vertical_seams, num_horizontal_seams,
               progress_callback=None, expand=False):
    # ----------------  VERTICAL  ----------------
    if expand and num_vertical_seams:
        seams = []
        e = compute_energy(image)

        # FIND seams  –  step-by-step with visible progress
        if progress_callback:
            progress_callback(0, "Vertical", "find")
        for i in range(num_vertical_seams):
            if progress_callback:                # update BEFORE heavy work
                progress_callback(i, "Vertical", "find")
                QApplication.processEvents()
            seam = find_vertical_seam(e)
            seams.append(seam)
            # block energy in one vectorised go
            rows = np.arange(e.shape[0])
            e[rows, seam] = 1e6
            time.sleep(0.015)                    # tiny throttle for eye
        if progress_callback:
            progress_callback(num_vertical_seams, "Vertical", "find")

        # INSERT seams  –  step-by-step
        if progress_callback:
            progress_callback(0, "Vertical", "insert")
        image = insert_vertical_seam(image, seams)
        for k in range(1, num_vertical_seams + 1):
            if progress_callback:
                progress_callback(k, "Vertical", "insert")
                QApplication.processEvents()
            time.sleep(0.015)
    else:
        # SHRINK – removal loop (already step-by-step)
        for i in range(num_vertical_seams):
            e = compute_energy(image)
            seam = find_vertical_seam(e)
            image = remove_vertical_seam(image, seam)
            if progress_callback:
                progress_callback(i + 1, "Vertical")

    # ----------------  HORIZONTAL  ----------------
    if expand and num_horizontal_seams:
        seams = []
        e = compute_energy(image)

        # FIND
        if progress_callback:
            progress_callback(0, "Horizontal", "find")
        for i in range(num_horizontal_seams):
            if progress_callback:
                progress_callback(i, "Horizontal", "find")
                QApplication.processEvents()
            seam = find_horizontal_seam(e)
            seams.append(seam)
            cols = np.arange(e.shape[1])
            e[seam, cols] = 1e6
            time.sleep(0.015)
        if progress_callback:
            progress_callback(num_horizontal_seams, "Horizontal", "find")

        # INSERT
        if progress_callback:
            progress_callback(0, "Horizontal", "insert")
        image = insert_horizontal_seam(image, seams)
        for k in range(1, num_horizontal_seams + 1):
            if progress_callback:
                progress_callback(k, "Horizontal", "insert")
                QApplication.processEvents()
            time.sleep(0.015)
    else:
        # SHRINK
        for i in range(num_horizontal_seams):
            e = compute_energy(image)
            seam = find_horizontal_seam(e)
            image = remove_horizontal_seam(image, seam)
            if progress_callback:
                progress_callback(i + 1, "Horizontal")

    return image
