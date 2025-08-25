# --- START OF FILE The Sigil Scribe.py ---

import sys
import string
import math
from PIL import Image
import random
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox
)
from PySide6.QtGui import QPixmap, QFont, QImage, QCursor
from PySide6.QtCore import Qt, QPointF

# --- MODIFIED: New Interactive Widget for Fractals ---
class InteractiveFractalLabel(QLabel):
    def __init__(self, parent_app, idx, width, height):
        super().__init__()
        self.parent_app = parent_app
        self.idx = idx
        self.setFixedSize(width, height)
        self.setObjectName("FractalImageLabel")

        # Interaction State
        self.is_dragging = False
        self.last_mouse_pos = QPointF()

        # Fractal State
        self.c_real = None
        self.c_imag = None
        self.palette = []
        self.reset_view()

    def set_params(self, c_real, c_imag, palette):
        """Sets the core Julia parameters and palette for this fractal."""
        self.c_real = c_real
        self.c_imag = c_imag
        self.palette = palette
        self.reset_view()
        self.regenerate()

    def reset_view(self):
        """Resets the zoom and pan to the default state."""
        self.re_center = 0.0
        self.im_center = 0.0
        self.re_span = 3.5  # Zoom level
        if self.c_real is not None:
            self.regenerate()

    def regenerate(self):
        """Generates and displays the fractal based on its current state."""
        if self.c_real is None or self.c_imag is None:
            return

        aspect_ratio = self.width() / self.height()
        im_span = self.re_span / aspect_ratio
        
        re_start = self.re_center - (self.re_span / 2)
        re_end = self.re_center + (self.re_span / 2)
        im_start = self.im_center - (im_span / 2)
        im_end = self.im_center + (im_span / 2)

        pil_img = self.parent_app.generate_julia_set(
            self.width(), self.height(), self.c_real, self.c_imag,
            self.parent_app.MAX_ITER, self.palette,
            re_start, re_end, im_start, im_end
        )
        
        # Update the main app's image list for saving
        self.parent_app.pil_images[self.idx] = pil_img
        
        pixmap = self.parent_app.pil_to_qpixmap(pil_img)
        self.setPixmap(pixmap)

    # --- Mouse Event Handlers for Interactivity ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.position() - self.last_mouse_pos
            self.last_mouse_pos = event.position()
            
            # Convert pixel delta to coordinate delta
            dx = (delta.x() / self.width()) * self.re_span
            dy = (delta.y() / self.height()) * (self.re_span / (self.width() / self.height()))
            
            self.re_center -= dx
            self.im_center -= dy
            self.regenerate()

    def wheelEvent(self, event):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        
        # Get mouse position in complex coordinates
        mouse_pos = event.position()
        aspect_ratio = self.width() / self.height()
        im_span = self.re_span / aspect_ratio
        mouse_re = self.re_center - (self.re_span / 2) + (mouse_pos.x() / self.width()) * self.re_span
        mouse_im = self.im_center - (im_span / 2) + (mouse_pos.y() / self.height()) * im_span

        # Adjust center to keep mouse position fixed
        self.re_center = mouse_re + (self.re_center - mouse_re) / zoom_factor
        self.im_center = mouse_im + (self.im_center - mouse_im) / zoom_factor
        
        # Apply zoom
        self.re_span /= zoom_factor
        self.regenerate()

    def mouseDoubleClickEvent(self, event):
        self.reset_view()

class SigilScribeApp(QMainWindow):
    FRACTAL_WIDTH = 200
    FRACTAL_HEIGHT = 150
    MAX_ITER = 150
    NUM_BASE_RANDOM_COLORS = 16
    NUM_FRACTALS = 5

    def __init__(self):
        super().__init__()
        self.palettes = [[] for _ in range(self.NUM_FRACTALS)]
        self.pil_images = [None] * self.NUM_FRACTALS
        self.setWindowTitle("The Sigil Scribe - Glyphs & Penta-Fractal Seeds")
        self.setGeometry(100, 100, 1400, 450)
        self.BG_COLOR = '#2E2E2E'
        self.setup_styling()
        self.setup_ui()
        self.center_window()

    def setup_styling(self):
        FG_COLOR = '#E0E0E0'
        ENTRY_BG = '#3C3F41'
        ENTRY_FG = 'white'
        BUTTON_BG_SECONDARY = '#4A4A4A'
        BUTTON_FG_SECONDARY = 'white'
        BUTTON_ACTIVE_SECONDARY = '#5A5A5A'
        ACCENT_COLOR = '#7B1FA2'
        ACCENT_ACTIVE = '#9C27B0'
        RESULT_BG = '#252526'
        RESULT_FG = '#D4D4D4'
        FRACTAL_LABEL_FG = '#C0C0C0'
        BORDER_COLOR_FOCUS = ACCENT_COLOR
        STYLESHEET = f"""
            QMainWindow, QWidget {{ background-color: {self.BG_COLOR}; color: {FG_COLOR}; font-family: Georgia; }}
            QLabel {{ font-size: 10pt; }}
            QLabel#FractalTitle {{ color: {FRACTAL_LABEL_FG}; font-size: 9pt; font-style: italic; }}
            QLabel#ResultLabel {{ background-color: {RESULT_BG}; color: {RESULT_FG}; font-family: "Courier New", monospace; font-size: 9pt; font-weight: bold; padding: 4px; border: 1px solid #444; border-radius: 3px; }}
            QLabel#FractalImageLabel {{ background-color: #1E1E1E; border: 1px solid #555; }}
            QLineEdit {{ background-color: {ENTRY_BG}; color: {ENTRY_FG}; font-family: "Segoe UI"; font-size: 10pt; border: 1px solid #555; border-radius: 3px; padding: 3px; }}
            QLineEdit:focus {{ border: 1px solid {BORDER_COLOR_FOCUS}; }}
            QPushButton#CopyButton, QPushButton#SaveButton {{ background-color: {BUTTON_BG_SECONDARY}; color: {BUTTON_FG_SECONDARY}; font-size: 8pt; padding: 3px 8px; border-radius: 3px; border: 1px solid #666; }}
            QPushButton#CopyButton:hover, QPushButton#SaveButton:hover {{ background-color: {BUTTON_ACTIVE_SECONDARY}; }}
            QPushButton#AccentButton {{ background-color: {ACCENT_COLOR}; color: white; font-size: 11pt; font-weight: bold; padding: 6px; border-radius: 3px; border: none; }}
            QPushButton#AccentButton:hover {{ background-color: {ACCENT_ACTIVE}; }}
        """
        self.setStyleSheet(STYLESHEET)

    def pil_to_qpixmap(self, pil_img):
        if pil_img.mode != "RGBA": pil_img = pil_img.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        q_img = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(q_img)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Panel ---
        steps_panel = QWidget()
        steps_layout = QVBoxLayout(steps_panel)
        steps_layout.setContentsMargins(0,0,0,0); steps_layout.setSpacing(5)
        steps_layout.addWidget(QLabel("Statement of Intent (Seed for Fractal 0):"))
        self.intent_entry = QLineEdit()
        self.intent_entry.returnPressed.connect(self.process_intent)
        steps_layout.addWidget(self.intent_entry)
        self.process_button = QPushButton("Scribe & Generate Fractals")
        self.process_button.setObjectName("AccentButton")
        self.process_button.clicked.connect(self.process_intent)
        steps_layout.addWidget(self.process_button)
        steps_layout.addSpacing(10)
        self.result_labels = []
        steps_data_labels = ["Step 1: Unique Letters", "Step 2: Vowels Removed", "Step 3: Numerological Reduction", "Step 4: Final Numerological Sum"]
        fractal_seed_source_labels = ["(Seed for Fractal 1)", "(Seed for Fractal 2)", "(Seed for Fractal 3)", "(Seed for Fractal 4)"]
        for i in range(4):
            steps_layout.addWidget(QLabel(f"{steps_data_labels[i]} {fractal_seed_source_labels[i]}".strip()))
            result_line_layout = QHBoxLayout()
            result_label = QLabel("...")
            result_label.setObjectName("ResultLabel")
            self.result_labels.append(result_label)
            copy_button = QPushButton("Copy")
            copy_button.setObjectName("CopyButton")
            copy_button.clicked.connect(lambda checked=False, lbl=result_label: self.copy_to_clipboard(lbl.text()))
            result_line_layout.addWidget(result_label, 1)
            result_line_layout.addWidget(copy_button)
            steps_layout.addLayout(result_line_layout)
            steps_layout.addSpacing(3)
        steps_layout.addStretch()
        self.save_all_button = QPushButton("Save All Fractals")
        self.save_all_button.setObjectName("AccentButton")
        self.save_all_button.setEnabled(False)
        self.save_all_button.clicked.connect(self.save_all_fractals_dialog)
        steps_layout.addWidget(self.save_all_button)
        steps_panel.setFixedWidth(380)
        main_layout.addWidget(steps_panel)

        # --- Right Panel ---
        fractals_panel = QWidget()
        fractals_layout = QHBoxLayout(fractals_panel)
        fractals_layout.setSpacing(10)
        self.fractal_label_widgets = []
        self.save_button_widgets = []
        fractal_titles = ["Fractal 0 (Raw Intent)", "Fractal 1 (Unique)", "Fractal 2 (No Vowels)", "Fractal 3 (Numeric)", "Fractal 4 (Sum)"]

        for i in range(self.NUM_FRACTALS):
            # MODIFIED: Use a container widget for vertical centering
            fractal_container = QWidget()
            fractal_box = QVBoxLayout(fractal_container)
            fractal_box.setContentsMargins(0,0,0,0)
            fractal_box.setSpacing(4)
            
            title_label = QLabel(fractal_titles[i])
            title_label.setObjectName("FractalTitle")
            title_label.setAlignment(Qt.AlignCenter)
            
            # Use the new interactive label
            image_label = InteractiveFractalLabel(self, i, self.FRACTAL_WIDTH, self.FRACTAL_HEIGHT)
            self.fractal_label_widgets.append(image_label)
            
            save_btn = QPushButton(f"Save F{i}")
            save_btn.setObjectName("SaveButton")
            save_btn.setEnabled(False)
            save_btn.clicked.connect(lambda checked=False, idx=i, title=fractal_titles[i]: self.save_image_dialog(
                self.pil_images[idx], f"fractal_{idx}_{title.split('(')[0].strip().lower().replace(' ','_')}.png"))
            self.save_button_widgets.append(save_btn)
            
            # MODIFIED: Add stretches for vertical centering
            fractal_box.addStretch()
            fractal_box.addWidget(title_label)
            fractal_box.addWidget(image_label)
            fractal_box.addWidget(save_btn)
            fractal_box.addStretch()
            
            fractals_layout.addWidget(fractal_container)

        main_layout.addWidget(fractals_panel, 1)
        self.clear_fractal_displays()

    def center_window(self):
        if self.isMaximized() or self.isFullScreen(): return
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def _generate_random_extended_palette(self):
        base_palette = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(self.NUM_BASE_RANDOM_COLORS)]
        if not base_palette: base_palette.append((random.randint(50,200), random.randint(50,200), random.randint(50,200)))
        return [base_palette[i % len(base_palette)] for i in range(self.MAX_ITER + 1)]

    def copy_to_clipboard(self, text):
        if not text or text == "...":
            QMessageBox.warning(self, "Nothing to Copy", "There is no text to copy.")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied!", f"'{text}' has been copied.")

    def simplify_number(self, num):
        s_num = str(num)
        while len(s_num) > 1: s_num = str(sum(int(digit) for digit in s_num))
        return int(s_num)

    def clear_fractal_displays(self):
        blank_pil_image = Image.new("RGB", (self.FRACTAL_WIDTH, self.FRACTAL_HEIGHT), self.BG_COLOR)
        blank_pixmap = self.pil_to_qpixmap(blank_pil_image)
        for i in range(self.NUM_FRACTALS):
            self.pil_images[i] = None
            self.fractal_label_widgets[i].setPixmap(blank_pixmap)
            self.fractal_label_widgets[i].c_real = None # Prevent regeneration
            self.save_button_widgets[i].setEnabled(False)
        self.save_all_button.setEnabled(False)

    def process_intent(self):
        raw_intent_text = self.intent_entry.text()
        if not raw_intent_text.strip():
            QMessageBox.warning(self, "Empty Intent", "Please enter a Statement of Intent.")
            return
        
        self.clear_fractal_displays()
        intent_upper = raw_intent_text.upper()
        
        for i in range(self.NUM_FRACTALS): self.palettes[i] = self._generate_random_extended_palette()
        processed_s1 = "".join(dict.fromkeys(c for c in intent_upper if c.isalpha()))
        self.result_labels[0].setText(processed_s1 or " ")
        processed_s2 = "".join(c for c in processed_s1 if c not in "AEIOU")
        self.result_labels[1].setText(processed_s2 or " ")
        numeric_s3 = "".join(str(self.simplify_number(ord(c) - ord('A') + 1)) for c in processed_s2) if processed_s2 else ""
        self.result_labels[2].setText(numeric_s3 or " ")
        final_sum_s4_str = str(self.simplify_number(sum(int(d) for d in numeric_s3))) if numeric_s3 else ""
        self.result_labels[3].setText(final_sum_s4_str or " ")
        seeds = [raw_intent_text, processed_s1, processed_s2, numeric_s3, final_sum_s4_str]
        param_funcs = [self.derive_julia_params_from_string] * 3 + [self.derive_julia_params_from_numeric_string, self.derive_julia_params_from_number_str]
        
        any_fractal_generated = False
        for i, (seed_val, param_func, palette) in enumerate(zip(seeds, param_funcs, self.palettes)):
            if seed_val:
                c_real, c_imag = param_func(seed_val)
                if c_real is not None and c_imag is not None:
                    # MODIFIED: Delegate regeneration to the interactive label
                    self.fractal_label_widgets[i].set_params(c_real, c_imag, palette)
                    self.save_button_widgets[i].setEnabled(True)
                    any_fractal_generated = True
        
        if any_fractal_generated: self.save_all_button.setEnabled(True)

    def derive_julia_params_from_string(self, text_seed):
        if not text_seed: return None, None
        alpha_seed = "".join(c for c in text_seed.upper() if c.isalpha())
        if not alpha_seed: return None, None
        s1 = sum(ord(c) - ord('A') + 1 for c in alpha_seed); p1 = 1; l1 = len(alpha_seed)
        text_hash_factor = sum(ord(c) for c in text_seed)
        for i, c in enumerate(alpha_seed):
            p1 = (p1 * (ord(c) - ord('A') + 1 + i*3 + l1 + (text_hash_factor % (i+10))))
            if p1 > 10**12 : p1 = (p1 % (10**9 + 7)) + (i+1) + s1 + (text_hash_factor % 100)
        c_real = -1.8 + ((s1 + p1 + l1*7 + text_hash_factor) % 3600) / 1000.0
        c_imag = -1.8 + ((s1 * l1 + (p1 // (l1*2+1 if l1 else 1)) + s1*3 + l1*5 + text_hash_factor*2) % 3600) / 1000.0
        return max(-2.0, min(2.0, c_real)), max(-2.0, min(2.0, c_imag))

    def derive_julia_params_from_numeric_string(self, numeric_string_seed):
        if not numeric_string_seed or not numeric_string_seed.isdigit(): return None, None
        s1 = sum(int(d) for d in numeric_string_seed); p1 = 1; l1 = len(numeric_string_seed)
        text_hash_factor = int(numeric_string_seed) if len(numeric_string_seed) < 10 else sum(int(d) for d in numeric_string_seed[:9])
        for i, d_char in enumerate(numeric_string_seed):
            d_val = int(d_char); p1 = (p1 * (d_val + 1 + i*2 + l1 + (text_hash_factor % (i+5))))
            if p1 > 10**12: p1 = (p1 % (10**9 + 9)) + (i+1) + s1 + (text_hash_factor % 50)
        c_real = -1.7 + ((s1 + p1 + l1*5 + text_hash_factor) % 3400) / 1000.0
        c_imag = -1.7 + ((s1 * l1 + (p1 // (l1*3+1 if l1 else 1)) + s1*6 + l1*3 + text_hash_factor*3) % 3400) / 1000.0
        return max(-2.0, min(2.0, c_real)), max(-2.0, min(2.0, c_imag))

    def derive_julia_params_from_number_str(self, num_seed_str):
        if not num_seed_str or not num_seed_str.isdigit(): return None, None
        num_seed = int(num_seed_str)
        if not (0 <= num_seed <= 9): return -0.8, 0.156
        known_c_values = [ (0.285, 0.01), (-0.70176, -0.3842), (-0.123, 0.745), (-0.8, 0.156), (-0.4, 0.6), (-0.74543, 0.11301), (0.32, 0.043), (-0.75, 0.11), (-0.835, -0.2321), (0.355534, -0.337292) ]
        return known_c_values[num_seed % len(known_c_values)]

    def generate_julia_set(self, width, height, c_real, c_imag, max_iter, color_palette, re_start, re_end, im_start, im_end):
        img = Image.new("RGB", (width, height), "black")
        pixels = img.load()
        for Px in range(width):
            for Py in range(height):
                # MODIFIED: Use view parameters instead of fixed calculations
                zx = re_start + (Px / width) * (re_end - re_start)
                zy = im_start + (Py / height) * (im_end - im_start)
                iteration = 0
                while zx*zx + zy*zy < 4 and iteration < max_iter:
                    xtemp = zx*zx - zy*zy + c_real
                    zy = 2*zx*zy + c_imag
                    zx = xtemp
                    iteration += 1
                if iteration == max_iter: pixels[Px, Py] = (0,0,0)
                elif color_palette: pixels[Px, Py] = color_palette[iteration % len(color_palette)]
                else: pixels[Px, Py] = (100,100,100)
        return img

    def save_image_dialog(self, pil_image_to_save, default_filename="fractal_sigil.png"):
        if not pil_image_to_save:
            QMessageBox.warning(self, "No Image", "No fractal image to save.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Fractal As", default_filename, "PNG Images (*.png);;All Files (*)")
        if filepath:
            try:
                pil_image_to_save.save(filepath)
                QMessageBox.information(self, "Saved", f"Successfully saved to:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save image:\n{e}")

    def save_all_fractals_dialog(self):
        generated_images = [(i, img) for i, img in enumerate(self.pil_images) if img is not None]
        if not generated_images:
            QMessageBox.warning(self, "No Images", "No fractals generated to save.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save All Fractals")
        if not directory: return
        fractal_titles = ["raw_intent", "unique_letters", "vowels_removed", "numeric_string", "final_sum"]
        saved_count = 0
        for idx, pil_image in generated_images:
            filename = f"fractal_{idx}_{fractal_titles[idx]}.png"
            filepath = os.path.join(directory, filename)
            try:
                pil_image.save(filepath); saved_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save {filename}:\n{e}")
        if saved_count > 0: QMessageBox.information(self, "Saved All", f"{saved_count} fractal(s) saved to:\n{directory}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Georgia", 10))
    window = SigilScribeApp()
    window.show()
    sys.exit(app.exec())