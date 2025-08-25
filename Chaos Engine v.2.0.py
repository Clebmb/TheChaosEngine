# Gnostic Visualizer v6.8 - The Resilient Oracle
#
# FINAL ROBUSTNESS UPGRADE:
# - GRACEFUL DEGRADATION: The Quantum Oracle is now resilient to network failures.
#   - If the ANU server cannot be reached, the UI will clearly display a network error.
#   - The system will then automatically generate a high-quality PSEUDO-random number locally to
#     use as a temporary seed.
# - CONTINUOUS OPERATION: This ensures the "Oracle" number continues to fluctuate chaotically
#   every second, even if the internet connection is down, making the tool more reliable.
# - AUTO-RECONNECT: The application will continue to attempt to fetch a true quantum seed on its
#   regular 30-second cycle, automatically switching back from the fallback when the connection
#   is restored.
#
# This is the ultimate, stable, and complete version.
#
import sys
import time
import hashlib
import random
import numpy as np
from numba import jit
import math
import os
import shutil
import string
import subprocess

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGroupBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QCheckBox, QComboBox,
    QFileDialog, QSlider, QGridLayout, QMessageBox, QFrame, QStyle
)
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QFont
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, Slot, QPointF, QObject, Signal, QThread

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("Warning: requests library not found. Quantum Seed Generator will be disabled.")
    REQUESTS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    print("Warning: pygame library not found. Music playback will be disabled.")
    PYGAME_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    print("Warning: sounddevice library not found. Tone generation will be disabled.")
    SOUNDDEVICE_AVAILABLE = False

print("Script starting (v6.8 - The Resilient Oracle)...")

# --- Configuration (Defaults for initial state) ---
DEFAULT_WIDGET_WIDTH, DEFAULT_WIDGET_HEIGHT = 560, 420
RENDER_SCALE_FACTOR = 1.5; DEFAULT_MAX_ITER_BASE = 45
STROBE_INTERVAL_MS = 100; ANIMATION_INTERVAL_MS = 75
ANIMATION_DURATION_SEC = 15.0; ANIMATION_ZOOM_MAGNITUDE = 0.25
ANIMATION_PAN_MAGNITUDE_X = 0.04; ANIMATION_PAN_MAGNITUDE_Y = 0.04
INITIAL_SIGIL_SCALE_PERCENT = 100.0; SIGIL_FLASH_INTERVAL_MS = 200
SAMPLE_RATE = 44100; DEFAULT_TONE_FREQUENCY = 432.0
DEFAULT_TONE_VOLUME = 0.5; DEFAULT_MUSIC_VOLUME_PERCENT = 70
QUANTUM_FETCH_INTERVAL_MS = 30000 # Fetch new TRUE quantum seed every 30 seconds
ORACLE_UPDATE_INTERVAL_MS = 1000 # Update the DISPLAY number every 1 second

# --- Numba Optimized Functions ---
@jit(nopython=True, fastmath=True, cache=True)
def calculate_mandelbrot_iterations_numba(iteration_array, re_start, re_end, im_start, im_end, width, height, max_iter):
    for x_pixel in range(width):
        for y_pixel in range(height):
            c_real=re_start+(x_pixel/width)*(re_end-re_start); c_imag=im_start+(y_pixel/height)*(im_end-im_start)
            z_real,z_imag,n=0.0,0.0,0
            while n<max_iter:
                z_real_sq=z_real*z_real; z_imag_sq=z_imag*z_imag
                if z_real_sq+z_imag_sq>4.0:break
                z_imag=2.0*z_real*z_imag+c_imag; z_real=z_real_sq-z_imag_sq+c_real; n+=1
            iteration_array[y_pixel,x_pixel]=n
    return iteration_array

@jit(nopython=True, fastmath=True, cache=True)
def calculate_julia_iterations_numba(iteration_array, re_start, re_end, im_start, im_end, width, height, max_iter, c_param_real, c_param_imag):
    for x_pixel in range(width):
        for y_pixel in range(height):
            z_real=re_start+(x_pixel/width)*(re_end-re_start); z_imag=im_start+(y_pixel/height)*(im_end-im_start); n=0
            while n<max_iter:
                z_real_sq=z_real*z_real; z_imag_sq=z_imag*z_imag
                if z_real_sq+z_imag_sq>4.0:break
                z_imag=2.0*z_real*z_imag+c_param_imag; z_real=z_real_sq-z_imag_sq+c_param_real; n+=1
            iteration_array[y_pixel,x_pixel]=n
    return iteration_array

@jit(nopython=True, fastmath=True, cache=True)
def calculate_burning_ship_iterations_numba(iteration_array, re_start, re_end, im_start, im_end, width, height, max_iter):
    for x_pixel in range(width):
        for y_pixel in range(height):
            c_real=re_start+(x_pixel/width)*(re_end-re_start); c_imag=im_start+(y_pixel/height)*(im_end-im_start)
            z_real,z_imag,n=0.0,0.0,0
            while n<max_iter:
                abs_z_real=abs(z_real); abs_z_imag=abs(z_imag)
                if (z_real*z_real+z_imag*z_imag)>4.0:break
                z_real_temp=(abs_z_real*abs_z_real)-(abs_z_imag*abs_z_imag)+c_real
                z_imag=2.0*abs_z_real*abs_z_imag+c_imag
                z_real=z_real_temp; n+=1
            iteration_array[y_pixel,x_pixel]=n
    return iteration_array

@jit(nopython=True, fastmath=True, cache=True)
def apply_sobel_filter(input_array, output_array):
    height, width = input_array.shape
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            gx = (input_array[y-1,x+1]+2*input_array[y,x+1]+input_array[y+1,x+1])-(input_array[y-1,x-1]+2*input_array[y,x-1]+input_array[y+1,x-1])
            gy = (input_array[y-1,x-1]+2*input_array[y-1,x]+input_array[y-1,x+1])-(input_array[y+1,x-1]+2*input_array[y+1,x]+input_array[y+1,x+1])
            output_array[y, x] = math.sqrt(gx**2 + gy**2)
    return output_array

@jit(nopython=True, fastmath=True, cache=True)
def apply_emboss_filter(input_array, output_array):
    height, width = input_array.shape
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            val = (-2*input_array[y-1,x-1] - input_array[y-1,x] + 0*input_array[y-1,x+1] \
                   -1*input_array[y,  x-1] + 1*input_array[y,  x] + 1*input_array[y,  x+1] \
                   +0*input_array[y+1,x-1] + 1*input_array[y+1,x] + 2*input_array[y+1,x+1])
            output_array[y, x] = val
    return output_array

@jit(nopython=True, cache=True)
def get_color_tuple_numba(n_iter_val, max_iter_val, palette_id_val, params):
    r_mult, g_mult, b_mult = params
    if n_iter_val == max_iter_val: return (0,0,0)
    r_val,g_val,b_val=0,0,0; n_calc=float(n_iter_val); pid = palette_id_val % 4
    if pid == 0: r_val=int(min(255.0,n_calc*r_mult)); g_val=int(min(255.0,n_calc*(g_mult+(n_iter_val%5)))); b_val=int(max(0.0,50.0-n_calc*b_mult))
    elif pid == 1: r_val=int(max(0.0,100.0-n_calc*r_mult)); g_val=int(min(255.0,n_calc*g_mult)); b_val=int(min(255.0,100.0+n_calc*b_mult))
    elif pid == 2: r_val=int(n_calc*r_mult+float(pid*30))%256; g_val=int(n_calc*g_mult+float(pid*60))%256; b_val=int(n_calc*b_mult)%100
    else: val_gs=int(255.0*n_calc/float(max_iter_val)); r_val,g_val,b_val=val_gs,val_gs,val_gs
    return(max(0,min(255,r_val)),max(0,min(255,g_val)),max(0,min(255,b_val)))

@jit(nopython=True, cache=True)
def get_color_tuple_trippy_numba(n_iter_val, max_iter_val, time_phase, params):
    hue_speed, sat_speed, val_speed, hue_offset, sat_offset, val_offset = params
    if n_iter_val == max_iter_val: return (0, 0, 0)
    hue = (n_iter_val / 25.0 + time_phase * hue_speed + hue_offset) % 1.0; saturation = 0.6 + math.sin(time_phase * 2.0 * math.pi * sat_speed + sat_offset) * 0.4
    value = 0.8 + math.sin(n_iter_val / 10.0 + time_phase * 2.0 * math.pi * val_speed + val_offset) * 0.2
    i = int(hue * 6.0); f = hue * 6.0 - i; p = value * (1.0 - saturation); q = value * (1.0 - f * saturation); t = value * (1.0 - (1.0 - f) * saturation); i %= 6
    if i == 0: r, g, b = value, t, p
    elif i == 1: r, g, b = q, value, p
    elif i == 2: r, g, b = p, value, t
    elif i == 3: r, g, b = p, q, value
    elif i == 4: r, g, b = t, p, value
    else: r, g, b = value, p, q
    return (int(r * 255), int(g * 255), int(b * 255))

@jit(nopython=True, cache=True, parallel=False)
def apply_colors_to_iteration_data_numba(iteration_data, image_data_buffer, max_iter_val, palette_id_val, effects_tuple):
    (use_psychedelic_colors, use_warping_bands, use_tunnel_vision, use_pixel_glitch,
     use_color_crush, use_scan_lines, time_phase, rand_params) = effects_tuple
    (psych_params, warp_freq, warp_amp, tunnel_power, glitch_chance, crush_levels,
     palette_params, scan_spacing, scan_darkness) = rand_params

    height, width = iteration_data.shape; center_x, center_y = width / 2.0, height / 2.0; max_dist = math.sqrt(center_x**2 + center_y**2)
    crush_factor = 256.0 / crush_levels
    for y_idx in range(height):
        for x_idx in range(width):
            iter_count = iteration_data[y_idx, x_idx]
            if use_warping_bands and iter_count < max_iter_val:
                band_offset = math.sin(y_idx / warp_freq + time_phase * math.pi * 4.0) * warp_amp
                iter_count = max(0, iter_count + int(band_offset))
            if use_pixel_glitch and random.random() < glitch_chance: iter_count = random.randint(0, max_iter_val)
            if use_psychedelic_colors: r, g, b = get_color_tuple_trippy_numba(iter_count, max_iter_val, time_phase, psych_params)
            else: r, g, b = get_color_tuple_numba(iter_count, max_iter_val, palette_id_val, palette_params)
            if use_tunnel_vision:
                dist = math.sqrt((x_idx - center_x)**2 + (y_idx - center_y)**2); brightness = max(0.0, 1.0 - (dist / max_dist)**tunnel_power)
                r, g, b = int(r * brightness), int(g * brightness), int(b * brightness)
            if use_color_crush:
                r = int(int(r / crush_factor) * crush_factor); g = int(int(g / crush_factor) * crush_factor); b = int(int(b / crush_factor) * crush_factor)
            if use_scan_lines and y_idx % scan_spacing == 0:
                r, g, b = int(r * scan_darkness), int(g * scan_darkness), int(b * scan_darkness)
            image_data_buffer[y_idx, x_idx, 0] = r; image_data_buffer[y_idx, x_idx, 1] = g; image_data_buffer[y_idx, x_idx, 2] = b
    return image_data_buffer

def generate_fractal_view_params(intent_str, aspect_ratio, fractal_type="Mandelbrot"):
    global DEFAULT_MAX_ITER_BASE;
    if not intent_str: intent_str = f"{fractal_type} Default"
    hash_obj = hashlib.sha256(intent_str.encode()); hex_digest = hash_obj.hexdigest()
    zoom_hex = hex_digest[:4]; min_s,max_s = 0.001,3.5; re_s = min_s+(int(zoom_hex,16)/65535.0)*(max_s-min_s)
    if fractal_type == "Burning Ship": re_c_base = -0.5; im_c_base = -0.5; re_s = 2.8
    elif fractal_type == "Julia": re_c_base = 0.0; im_c_base = 0.0; re_s = 3.0
    else: re_c_base = -0.75; im_c_base = 0.0
    cx_offset_hex=hex_digest[4:8];cy_offset_hex=hex_digest[8:12];re_c_offset=(-0.5+(int(cx_offset_hex,16)/65535.0))*re_s*0.3;im_c_offset=(-0.5+(int(cy_offset_hex,16)/65535.0))*(re_s/aspect_ratio if aspect_ratio>0 else re_s)*0.3
    re_c=re_c_base+re_c_offset;im_c=im_c_base+im_c_offset;julia_c_real=-1.5+(int(hex_digest[20:24],16)/65535.0)*3.0;julia_c_imag=-1.5+(int(hex_digest[24:28],16)/65535.0)*3.0
    iter_hex=hex_digest[16:18];min_i_iter,max_i_iter_cfg=DEFAULT_MAX_ITER_BASE,int(DEFAULT_MAX_ITER_BASE*2.5);cur_max_i=min_i_iter+int((int(iter_hex,16)/255.0)*(max_i_iter_cfg-min_i_iter))
    return (re_s,re_c,im_c,cur_max_i,julia_c_real,julia_c_imag)if fractal_type=="Julia"else(re_s,re_c,im_c,cur_max_i,None,None)

# --- Background Workers ---
class QuantumWorker(QObject):
    success = Signal(int)
    error = Signal(str)

    @Slot()
    def run(self):
        if not REQUESTS_AVAILABLE:
            self.error.emit("requests library not found")
            return
        try:
            url = "https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint16"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                number = data['data'][0]
                self.success.emit(number)
            else:
                self.error.emit("API Error")
        except requests.exceptions.RequestException:
            self.error.emit("Network Error")

class ChaosWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, source_path, target_path, veil_target, dissolve_source):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path
        self.veil_target = veil_target
        self.dissolve_source = dissolve_source

    @Slot()
    def run(self):
        try:
            target_basename_original = os.path.basename(self.target_path)
            source_basename = os.path.basename(self.source_path)

            for item_name in os.listdir(self.target_path):
                item_path = os.path.join(self.target_path, item_name)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except Exception: pass
            shutil.copytree(self.source_path, self.target_path, dirs_exist_ok=True)
            final_message_part = f"Target '{target_basename_original}' imbued with content from '{source_basename}'."

            if self.veil_target:
                parent_locus = os.path.dirname(self.target_path)
                glyph_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
                new_path = os.path.join(parent_locus, glyph_name)
                while os.path.exists(new_path):
                    glyph_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
                    new_path = os.path.join(parent_locus, glyph_name)
                os.rename(self.target_path, new_path)
                final_message_part = f"The Target has been Veiled under the glyph: {glyph_name}"

            if self.dissolve_source:
                shutil.rmtree(self.source_path)
                final_message_part += f"\nThe Source '{source_basename}' has been dissolved."

            self.finished.emit(f"The Working is Complete.\n\n{final_message_part}")
        except Exception as e:
            self.error.emit(f"A discordant resonance! The Working faltered:\n\n{e}")

class FractalDisplayWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.main_window = parent
        self.setMinimumSize(DEFAULT_WIDGET_WIDTH,DEFAULT_WIDGET_HEIGHT); self.setStyleSheet("background-color:black;")
        self.fractal_pixmap=None; self.sigil_original_pixmap=None; self.sigil_initial_display_size=QSize(0,0); self.sigil_target_display_size=QSize(0,0); self.sigil_current_pos=QPoint(0,0); self.sigil_visible=False
        self._update_with_blank_fractal_pixmap(self.minimumWidth(),self.minimumHeight())
    def _update_with_blank_fractal_pixmap(self,width,height):
        blk=QImage(width,height,QImage.Format.Format_RGB32); blk.fill(Qt.GlobalColor.black); self.fractal_pixmap=QPixmap.fromImage(blk); self.update()
    def update_fractal_pixmap(self,pixmap):
        self.fractal_pixmap = pixmap if pixmap else self._update_with_blank_fractal_pixmap(self.width(),self.height()); self.update()
    def set_sigil_parameters(self,original_pixmap,initial_display_size,visible=True):
        self.sigil_original_pixmap=original_pixmap; self.sigil_initial_display_size=initial_display_size; self.sigil_target_display_size=initial_display_size; self.sigil_visible=visible and bool(original_pixmap); self.update()
    def update_sigil_position(self,position):
        self.sigil_current_pos=position; self.sigil_visible and self.update()
    def update_sigil_target_size(self, new_size):
        self.sigil_target_display_size = new_size; self.update()
    def paintEvent(self,event):
        super().paintEvent(event); painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.fractal_pixmap:
            sfp=self.fractal_pixmap.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            px=(self.width()-sfp.width())//2; py=(self.height()-sfp.height())//2
            if self.main_window.effect_states['rgb']:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                painter.setOpacity(0.5)
                painter.drawImage(px - self.main_window.rgb_shift_amount, py, sfp.toImage())
                painter.drawImage(px, py - self.main_window.rgb_shift_amount, sfp.toImage())
                painter.drawImage(px + self.main_window.rgb_shift_amount, py, sfp.toImage())
            else: painter.drawPixmap(px,py,sfp)
        else: painter.fillRect(self.rect(),QColor("black"))
        if self.sigil_visible and self.sigil_original_pixmap: ss=self.sigil_original_pixmap.scaled(self.sigil_target_display_size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation); painter.drawPixmap(self.sigil_current_pos,ss)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.main_window.is_dragging = True; self.main_window.last_mouse_pos = event.position(); self.setCursor(Qt.CursorShape.ClosedHandCursor)
    def mouseMoveEvent(self, event):
        if self.main_window.is_dragging: delta = event.position() - self.main_window.last_mouse_pos; self.main_window.pan_fractal_view(delta); self.main_window.last_mouse_pos = event.position()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.main_window.is_dragging = False; self.setCursor(Qt.CursorShape.ArrowCursor)
    def wheelEvent(self, event):
        self.main_window.zoom_fractal_view(event.angleDelta().y(), event.position())

class MainWindow(QMainWindow):
    _tone_data_pos = 0
    def __init__(self):
        super().__init__(); self.render_scale_factor=RENDER_SCALE_FACTOR
        self.setWindowTitle(f"Chaos Engine 2.6.1 - Gnosis Visualizer - Made By Cleb (and Gemini)");
        self.initial_intent_string="Write Your Intent Here..."; self.iteration_data_np=None; self.edge_data_np=None; self.image_data_buffer_np=None; self.coloring_data_source=None
        self.base_view_params={'re_span':3.5,'re_center':-0.5,'im_center':0.0}; self.base_max_iter=DEFAULT_MAX_ITER_BASE
        self.julia_c_params=(0.,0.); self.current_fractal_type="Mandelbrot"; self.current_max_iter_anim=DEFAULT_MAX_ITER_BASE
        self.sigil_original_pixmap=None; self.sigil_current_scale_percent=INITIAL_SIGIL_SCALE_PERCENT; self.is_animating_fractal=True
        self.palette_id_counter=0; self.num_palettes=4; self.is_dragging = False; self.last_mouse_pos = QPointF(); self.current_time_phase = 0.0
        self._init_effects_state_and_params()
        self.chaos_thread = None; self.chaos_worker = None
        self.q_thread = None; self.q_worker = None
        self.base_quantum_seed = 0 # This will hold the true random seed
        self.sigil_flash_timer=QTimer(self); self.sigil_flash_timer.timeout.connect(self.update_sigil_flash_position)
        self.animation_timer=QTimer(self); self.animation_timer.timeout.connect(self.update_animated_fractal_structure); self.animation_start_time=time.time()
        self.strobe_timer=QTimer(self); self.strobe_timer.timeout.connect(self.apply_new_palette_and_render)
        if PYGAME_AVAILABLE: pygame.init(); pygame.mixer.init(); self.is_music_paused = False
        if SOUNDDEVICE_AVAILABLE: self.tone_stream=None; self.current_tone_frequency=DEFAULT_TONE_FREQUENCY; self.tone_volume=DEFAULT_TONE_VOLUME; self.is_tone_playing=False
        try: self.script_dir=os.path.dirname(os.path.abspath(__file__))
        except NameError: self.script_dir=os.getcwd()
        self.predefined_tracks={"Track 1":os.path.join(self.script_dir,"track1.mp3"),"Track 2":os.path.join(self.script_dir,"track2.mp3"),"Track 3":os.path.join(self.script_dir,"track3.mp3")}
        self.uploaded_track_path=None
        self._setup_ui()
        self.resize(self.minimumSizeHint()) # Open at the smallest possible size
        self.music_status_timer = QTimer(self); self.music_status_timer.timeout.connect(self.update_music_button_state); self.music_status_timer.start(250)

        # --- Timers for the Quantum Oracle ---
        self.quantum_fetch_timer = QTimer(self); self.quantum_fetch_timer.timeout.connect(self.fetch_quantum_seed); self.quantum_fetch_timer.start(QUANTUM_FETCH_INTERVAL_MS)
        self.oracle_update_timer = QTimer(self); self.oracle_update_timer.timeout.connect(self.update_oracle_display); self.oracle_update_timer.start(ORACLE_UPDATE_INTERVAL_MS)

        QTimer.singleShot(50, self.trigger_full_regeneration_from_intent)
        QTimer.singleShot(100, self.fetch_quantum_seed) # Initial fetch
        print("MainWindow __init__ finished.")

    def _init_effects_state_and_params(self):
        self.effect_states = {k: False for k in ['colors', 'bands', 'tunnel', 'glitch', 'morph', 'neon', 'rgb', 'crush', 'emboss', 'scan', 'strobe']}
        self.previous_effect_states = self.effect_states.copy()
        self.psych_params = (2.0, 3.0, 1.0, 0.0, 0.0, 0.0); self.warping_bands_freq = 30.0; self.warping_bands_amp = 10.0
        self.tunnel_power = 2.0; self.pixel_glitch_chance = 0.001; self.color_crush_levels = 4; self.rgb_shift_amount = 2
        self.julia_morph_radius = 0.005; self.palette_params = (15.0, 5.0, 2.0); self.scan_line_spacing = 4; self.scan_line_darkness = 0.7

    def _randomize_effect_parameters(self, effect_name):
        if effect_name == 'colors': self.psych_params = (random.uniform(1,4), random.uniform(1,4), random.uniform(0.5,2), random.random(), random.random(), random.random())
        elif effect_name == 'bands': self.warping_bands_freq = random.uniform(15, 60); self.warping_bands_amp = random.uniform(5, 15)
        elif effect_name == 'tunnel': self.tunnel_power = random.uniform(1.5, 3.5)
        elif effect_name == 'glitch': self.pixel_glitch_chance = random.uniform(0.0005, 0.0025)
        elif effect_name == 'crush': self.color_crush_levels = random.randint(3, 8)
        elif effect_name == 'rgb': self.rgb_shift_amount = random.randint(1, 4)
        elif effect_name == 'morph': self.julia_morph_radius = random.uniform(0.002, 0.01)
        elif effect_name in ['neon', 'emboss']: self.palette_params = (random.uniform(5,20), random.uniform(2,10), random.uniform(1,5))
        elif effect_name == 'scan': self.scan_line_spacing = random.randint(3, 6); self.scan_line_darkness = random.uniform(0.5, 0.8)

    def _setup_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget); main_layout.setContentsMargins(5,5,5,5); main_layout.setSpacing(2)

        # --- Quantum Seed Bar ---
        q_bar = QWidget(); q_bar_layout = QHBoxLayout(q_bar); q_bar_layout.setContentsMargins(5, 0, 5, 0)
        self.quantum_seed_label = QLabel("Quantum Seed: [Fetching...]")
        self.oracle_value_label = QLabel("Oracle: ---")
        separator = QLabel("|")

        for label in [self.quantum_seed_label, self.oracle_value_label, separator]:
            font = label.font(); font.setPointSize(9); font.setBold(True); label.setFont(font)
            label.setAlignment(Qt.AlignCenter)

        self.help_button = QPushButton(); self.help_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)); self.help_button.setFixedSize(20, 20); self.help_button.clicked.connect(self.show_quantum_help)
        q_bar_layout.addStretch()
        q_bar_layout.addWidget(self.quantum_seed_label)
        q_bar_layout.addWidget(separator)
        q_bar_layout.addWidget(self.oracle_value_label)
        q_bar_layout.addStretch()
        q_bar_layout.addWidget(self.help_button)
        main_layout.addWidget(q_bar)

        self.fractal_display = FractalDisplayWidget(self); self.fractal_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.fractal_display, 1)

        # --- Master Control Grid ---
        controls_container = QWidget()
        grid = QGridLayout(controls_container)
        grid.setContentsMargins(5, 2, 5, 2); grid.setSpacing(4)

        # -- Column 0-3: Master Control & Sigil --
        grid.addWidget(QLabel("<b>Master & Sigil</b>"), 0, 0, 1, 4)
        self.intent_input = QLineEdit(self.initial_intent_string); self.intent_input.returnPressed.connect(self.trigger_full_regeneration_from_intent)
        grid.addWidget(self.intent_input, 1, 0, 1, 3)
        self.generate_button = QPushButton("Generate"); self.generate_button.clicked.connect(self.trigger_full_regeneration_from_intent)
        grid.addWidget(self.generate_button, 1, 3)
        self.fractal_type_combo = QComboBox(); self.fractal_type_combo.addItems(["Mandelbrot", "Julia", "Burning Ship"]); self.fractal_type_combo.currentTextChanged.connect(self.on_fractal_type_changed)
        grid.addWidget(self.fractal_type_combo, 2, 0, 1, 2)
        self.julia_c_real_input = QLineEdit("-0.7"); self.julia_c_imag_input = QLineEdit("0.27015")
        self.julia_c_widget = QWidget(); julia_c_layout = QHBoxLayout(self.julia_c_widget); julia_c_layout.setContentsMargins(0,0,0,0); julia_c_layout.addWidget(QLabel("C:")); julia_c_layout.addWidget(self.julia_c_real_input); julia_c_layout.addWidget(self.julia_c_imag_input)
        self.julia_c_widget.setVisible(False); grid.addWidget(self.julia_c_widget, 2, 2, 1, 2)
        perf_hlayout = QHBoxLayout(); perf_hlayout.setContentsMargins(0,0,0,0); perf_hlayout.setSpacing(2); perf_hlayout.addWidget(QLabel("Scale:")); self.scale_input = QLineEdit(str(self.render_scale_factor)); self.scale_input.setFixedWidth(35); perf_hlayout.addWidget(self.scale_input); perf_hlayout.addWidget(QLabel("Iter:")); self.max_iter_input = QLineEdit(str(DEFAULT_MAX_ITER_BASE)); self.max_iter_input.setFixedWidth(35); perf_hlayout.addWidget(self.max_iter_input); apply_perf_button = QPushButton("Set"); apply_perf_button.clicked.connect(self.apply_performance_settings); perf_hlayout.addWidget(apply_perf_button);
        grid.addLayout(perf_hlayout, 3, 0, 1, 4)
        self.import_sigil_button = QPushButton("Import"); self.import_sigil_button.clicked.connect(self.import_sigil)
        self.remove_sigil_button = QPushButton("Remove"); self.remove_sigil_button.clicked.connect(self.remove_sigil); self.remove_sigil_button.setEnabled(False)
        sigil_scale_layout = QHBoxLayout(); sigil_scale_layout.setContentsMargins(0,0,0,0); sigil_scale_layout.setSpacing(2); sigil_scale_layout.addWidget(QLabel("Scale:")); self.sigil_scale_input = QLineEdit(str(int(INITIAL_SIGIL_SCALE_PERCENT))); self.sigil_scale_input.setFixedWidth(35); self.sigil_scale_input.setEnabled(False); sigil_scale_layout.addWidget(self.sigil_scale_input); self.apply_sigil_scale_button = QPushButton("Set"); self.apply_sigil_scale_button.clicked.connect(self.apply_sigil_scale); self.apply_sigil_scale_button.setEnabled(False); sigil_scale_layout.addWidget(self.apply_sigil_scale_button)
        grid.addWidget(self.import_sigil_button, 4, 0); grid.addWidget(self.remove_sigil_button, 4, 1); grid.addLayout(sigil_scale_layout, 4, 2, 1, 2)

        # -- Vertical Separator --
        sep1 = QFrame(); sep1.setFrameShape(QFrame.VLine); sep1.setFrameShadow(QFrame.Sunken); grid.addWidget(sep1, 0, 4, 6, 1)

        # -- Column 5-7: Audio --
        grid.addWidget(QLabel("<b>Audio</b>"), 0, 5, 1, 3)
        self.music_track_combo = QComboBox(); self.music_track_combo.addItems(list(self.predefined_tracks.keys()))
        self.upload_music_button = QPushButton("..."); self.upload_music_button.setFixedWidth(25); self.upload_music_button.clicked.connect(self.upload_music_track)
        grid.addWidget(self.music_track_combo, 1, 5, 1, 2); grid.addWidget(self.upload_music_button, 1, 7)
        self.play_pause_music_button = QPushButton("Play / Pause"); self.play_pause_music_button.clicked.connect(self.toggle_play_pause_music)
        grid.addWidget(self.play_pause_music_button, 2, 5, 1, 3)
        self.music_volume_slider = QSlider(Qt.Orientation.Horizontal); self.music_volume_slider.setRange(0, 100); self.music_volume_slider.setValue(DEFAULT_MUSIC_VOLUME_PERCENT); self.music_volume_slider.valueChanged.connect(self.set_music_volume)
        grid.addWidget(self.music_volume_slider, 3, 5, 1, 3)
        tone_layout = QHBoxLayout(); tone_layout.setContentsMargins(0,0,0,0); tone_layout.setSpacing(2); self.tone_freq_input = QLineEdit(str(DEFAULT_TONE_FREQUENCY)); self.tone_freq_input.setFixedWidth(40); self.tone_freq_input.editingFinished.connect(self.update_tone_frequency); tone_layout.addWidget(self.tone_freq_input); self.play_tone_button = QPushButton("Play"); self.play_tone_button.clicked.connect(self.play_frequency_tone); tone_layout.addWidget(self.play_tone_button); self.stop_tone_button = QPushButton("Stop"); self.stop_tone_button.clicked.connect(self.stop_frequency_tone); self.stop_tone_button.setEnabled(False); tone_layout.addWidget(self.stop_tone_button)
        grid.addLayout(tone_layout, 4, 5, 1, 3)
        self.tone_volume_slider = QSlider(Qt.Orientation.Horizontal); self.tone_volume_slider.setRange(0, 100); self.tone_volume_slider.setValue(int(DEFAULT_TONE_VOLUME * 100)); self.tone_volume_slider.valueChanged.connect(self.set_tone_volume)
        grid.addWidget(self.tone_volume_slider, 5, 5, 1, 3)

        audio_group_for_enable = [self.music_track_combo, self.upload_music_button, self.play_pause_music_button, self.music_volume_slider]; [w.setEnabled(PYGAME_AVAILABLE) for w in audio_group_for_enable]
        tone_group_for_enable = [self.tone_freq_input, self.play_tone_button, self.stop_tone_button, self.tone_volume_slider]; [w.setEnabled(SOUNDDEVICE_AVAILABLE) for w in tone_group_for_enable]

        # -- Vertical Separator --
        sep2 = QFrame(); sep2.setFrameShape(QFrame.VLine); sep2.setFrameShadow(QFrame.Sunken); grid.addWidget(sep2, 0, 8, 6, 1)

        # -- Column 9-10: Effects --
        grid.addWidget(QLabel("<b>Visual Effects</b>"), 0, 9, 1, 2)
        effects_col1 = QVBoxLayout(); effects_col1.setContentsMargins(0,0,0,0); effects_col1.setSpacing(1)
        self.effect_strobe_checkbox = QCheckBox("Strobe"); self.effect_strobe_checkbox.stateChanged.connect(self.toggle_effects); effects_col1.addWidget(self.effect_strobe_checkbox)
        self.effect_colors_checkbox = QCheckBox("Psychedelic"); self.effect_colors_checkbox.stateChanged.connect(self.toggle_effects); effects_col1.addWidget(self.effect_colors_checkbox)
        self.effect_bands_checkbox = QCheckBox("Warp Bands"); self.effect_bands_checkbox.stateChanged.connect(self.toggle_effects); effects_col1.addWidget(self.effect_bands_checkbox)
        self.effect_scan_lines_checkbox = QCheckBox("Scan Lines"); self.effect_scan_lines_checkbox.stateChanged.connect(self.toggle_effects); effects_col1.addWidget(self.effect_scan_lines_checkbox)
        self.effect_rgb_shift_checkbox = QCheckBox("RGB Shift"); self.effect_rgb_shift_checkbox.stateChanged.connect(self.toggle_effects); effects_col1.addWidget(self.effect_rgb_shift_checkbox)
        grid.addLayout(effects_col1, 1, 9, 5, 1)

        effects_col2 = QVBoxLayout(); effects_col2.setContentsMargins(0,0,0,0); effects_col2.setSpacing(1)
        self.effect_neon_edges_checkbox = QCheckBox("Neon Edges"); self.effect_neon_edges_checkbox.stateChanged.connect(self.toggle_effects); effects_col2.addWidget(self.effect_neon_edges_checkbox)
        self.effect_emboss_checkbox = QCheckBox("Emboss"); self.effect_emboss_checkbox.stateChanged.connect(self.toggle_effects); effects_col2.addWidget(self.effect_emboss_checkbox)
        self.effect_color_crush_checkbox = QCheckBox("Color Crush"); self.effect_color_crush_checkbox.stateChanged.connect(self.toggle_effects); effects_col2.addWidget(self.effect_color_crush_checkbox)
        self.effect_pixel_glitch_checkbox = QCheckBox("Pixel Glitch"); self.effect_pixel_glitch_checkbox.stateChanged.connect(self.toggle_effects); effects_col2.addWidget(self.effect_pixel_glitch_checkbox)
        self.effect_morph_checkbox = QCheckBox("Julia Morph"); self.effect_morph_checkbox.stateChanged.connect(self.toggle_effects); effects_col2.addWidget(self.effect_morph_checkbox)
        grid.addLayout(effects_col2, 1, 10, 5, 1)

        # -- Vertical Separator --
        sep3 = QFrame(); sep3.setFrameShape(QFrame.VLine); sep3.setFrameShadow(QFrame.Sunken); grid.addWidget(sep3, 0, 11, 6, 1)

        # -- Column 12-14: Digital Alchemy & Scribe --
        grid.addWidget(QLabel("<b>Digital Alchemy</b>"), 0, 12, 1, 3)
        source_layout = QHBoxLayout(); source_layout.setContentsMargins(0,0,0,0); source_layout.setSpacing(2); self.source_path_input = QLineEdit(); self.source_path_input.setPlaceholderText("Source"); source_layout.addWidget(self.source_path_input); self.browse_source_button = QPushButton("..."); self.browse_source_button.setFixedWidth(25); self.browse_source_button.clicked.connect(self.browse_source_folder); source_layout.addWidget(self.browse_source_button)
        grid.addLayout(source_layout, 1, 12, 1, 3)
        target_layout = QHBoxLayout(); target_layout.setContentsMargins(0,0,0,0); target_layout.setSpacing(2); self.target_path_input = QLineEdit(); self.target_path_input.setPlaceholderText("Target"); target_layout.addWidget(self.target_path_input); self.browse_target_button = QPushButton("..."); self.browse_target_button.setFixedWidth(25); self.browse_target_button.clicked.connect(self.browse_target_folder); target_layout.addWidget(self.browse_target_button)
        grid.addLayout(target_layout, 2, 12, 1, 3)
        self.veil_target_checkbox = QCheckBox("Veil Target"); self.veil_target_checkbox.setChecked(True)
        self.dissolve_source_checkbox = QCheckBox("Dissolve Source")
        grid.addWidget(self.veil_target_checkbox, 3, 12); grid.addWidget(self.dissolve_source_checkbox, 3, 13, 1, 2)
        self.initiate_chaos_button = QPushButton("Initiate Working"); self.initiate_chaos_button.clicked.connect(self.start_chaos_working)
        grid.addWidget(self.initiate_chaos_button, 4, 12, 1, 3)

        # -- Global Controls (Animate, Save, Scribe)
        self.animate_checkbox = QCheckBox("Animate"); self.animate_checkbox.setChecked(self.is_animating_fractal); self.animate_checkbox.stateChanged.connect(self.toggle_fractal_animation)
        self.save_button = QPushButton("Save Fractal"); self.save_button.clicked.connect(self.save_fractal_image)
        self.open_scribe_button = QPushButton("Open Sigil Scribe"); self.open_scribe_button.clicked.connect(self.open_sigil_scribe)

        misc_layout = QHBoxLayout(); misc_layout.setContentsMargins(0,0,0,0); misc_layout.setSpacing(5); misc_layout.addWidget(self.animate_checkbox); misc_layout.addWidget(self.save_button); misc_layout.addStretch(); misc_layout.addWidget(self.open_scribe_button)
        grid.addLayout(misc_layout, 5, 0, 1, 4)

        grid.setColumnStretch(15, 1)
        main_layout.addWidget(controls_container)

    @Slot()
    def fetch_quantum_seed(self):
        if not REQUESTS_AVAILABLE:
            self.quantum_seed_label.setText("Quantum Seed: [requests library missing]")
            return
        if self.q_thread and self.q_thread.isRunning(): return

        self.quantum_seed_label.setText("Quantum Seed: [Fetching...]")
        self.q_thread = QThread()
        self.q_worker = QuantumWorker()
        self.q_worker.moveToThread(self.q_thread)
        self.q_thread.started.connect(self.q_worker.run)
        self.q_worker.success.connect(self.store_quantum_seed)
        self.q_worker.error.connect(self.handle_quantum_error)
        self.q_thread.finished.connect(self.q_worker.deleteLater)
        self.q_thread.finished.connect(self.q_thread.deleteLater)
        self.q_thread.finished.connect(self.on_q_thread_finished)
        self.q_thread.start()

    @Slot()
    def on_q_thread_finished(self):
        self.q_thread = None
        self.q_worker = None

    @Slot(int)
    def store_quantum_seed(self, number):
        self.base_quantum_seed = number
        self.quantum_seed_label.setText(f"Quantum Seed: {number}")
        print(f"New Quantum Seed acquired: {number}")
        if self.q_thread:
            self.q_thread.quit()

    @Slot(str)
    def handle_quantum_error(self, message):
        self.quantum_seed_label.setText(f"Quantum Seed: [Network Error - Using Fallback]")
        self.base_quantum_seed = random.randint(0, 65535) # Use pseudo-random fallback
        print(f"Quantum fetch error: {message}. Using pseudo-random fallback seed: {self.base_quantum_seed}")
        if self.q_thread:
            self.q_thread.quit()

    @Slot()
    def update_oracle_display(self):
        current_milli = int(time.time() * 1000)
        input_string = f"{self.base_quantum_seed}-{current_milli}"
        h = hashlib.sha256(input_string.encode()).hexdigest()
        display_number = int(h[:8], 16)
        self.oracle_value_label.setText(f"Oracle: {display_number}")

    @Slot()
    def show_quantum_help(self):
        help_text = (
            "<b>What is the Dual Oracle?</b><br><br>"
            "The top bar displays two numbers derived from true randomness using a hybrid system for a powerful, chaotic output.<br><br>"
            "1. <b>Quantum Seed:</b> This is a true random number fetched from the ANU Quantum Server. It updates every 30 seconds and acts as the non-deterministic anchor for the system. If the server cannot be reached, it uses a pseudo-random fallback and notifies you.<br><br>"
            "2. <b>Oracle:</b> This is the rapidly fluctuating number. Every second, it takes the current Quantum Seed, combines it with the system's millisecond time, and processes it through a cryptographic hash. This creates the wildly unpredictable number you see.<br><br>"
            "<b>How to use it in Chaos Magick:</b><br>"
            "<ul>"
            "<li><b>Breaking Patterns:</b> Use the rapidly changing <b>Oracle</b> number as a focal point during meditation to break out of rigid thought patterns.</li>"
            "<li><b>Sigil Charging:</b> Gaze at the fluctuating <b>Oracle</b> while charging a sigil to inject a stream of pure, chaotic potential into your intent.</li>"
            "<li><b>Divination:</b> Use a snapshot of the <b>Oracle</b> number for divinatory acts (e.g., Number % 22 for a Major Arcana card).</li>"
            "<li><b>Ritual Seed:</b> Use the static <b>Quantum Seed</b> to influence the core of a ritual (e.g., number of repetitions, etc.) for an outcome rooted in true chance.</li>"
            "</ul>"
        )
        QMessageBox.information(self, "About the Dual Oracle", help_text)

    @Slot()
    def open_sigil_scribe(self):
        scribe_script_name = "The Sigil Scribe.py"
        scribe_path = os.path.join(self.script_dir, scribe_script_name)
        if os.path.exists(scribe_path):
            try:
                print(f"Attempting to launch {scribe_path}...")
                subprocess.Popen([sys.executable, scribe_path])
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch '{scribe_script_name}':\n\n{e}")
        else:
            QMessageBox.warning(self, "File Not Found", f"The script '{scribe_script_name}' was not found in the application directory:\n\n{self.script_dir}")

    @Slot()
    def browse_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source of Intent Folder")
        if folder: self.source_path_input.setText(folder)
    @Slot()
    def browse_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Ritual Space (Target) Folder")
        if folder: self.target_path_input.setText(folder)

    @Slot()
    def start_chaos_working(self):
        source_path = self.source_path_input.text()
        target_path = self.target_path_input.text()

        if not source_path or not target_path:
            QMessageBox.critical(self, "Incomplete Invocation", "Both the Source and Target must be defined.")
            return
        if not os.path.isdir(source_path):
            QMessageBox.critical(self, "Illusory Source", f"The Source path does not exist or is not a directory:\n{source_path}")
            return
        if not os.path.isdir(target_path):
            QMessageBox.critical(self, "Unformed Space", f"The Target path does not exist or is not a directory:\n{target_path}")
            return
        if os.path.abspath(source_path) == os.path.abspath(target_path):
            QMessageBox.critical(self, "Paradoxical Invocation", "The Source and Target cannot be the same locus.")
            return

        self.initiate_chaos_button.setEnabled(False)
        self.initiate_chaos_button.setText("Working...")

        veil = self.veil_target_checkbox.isChecked()
        dissolve = self.dissolve_source_checkbox.isChecked()

        self.chaos_thread = QThread()
        self.chaos_worker = ChaosWorker(source_path, target_path, veil, dissolve)
        self.chaos_worker.moveToThread(self.chaos_thread)

        self.chaos_thread.started.connect(self.chaos_worker.run)
        self.chaos_worker.finished.connect(self.on_chaos_finished)
        self.chaos_worker.error.connect(self.on_chaos_error)

        self.chaos_worker.finished.connect(self.chaos_thread.quit)
        self.chaos_worker.finished.connect(self.chaos_worker.deleteLater)
        self.chaos_thread.finished.connect(self.chaos_thread.deleteLater)

        self.chaos_thread.start()

    @Slot(str)
    def on_chaos_finished(self, message):
        QMessageBox.information(self, "The Working is Complete", message)
        self.initiate_chaos_button.setEnabled(True)
        self.initiate_chaos_button.setText("Initiate Working")
        self.source_path_input.clear()
        self.target_path_input.clear()
        self.chaos_thread = None
        self.chaos_worker = None

    @Slot(str)
    def on_chaos_error(self, message):
        QMessageBox.critical(self, "A Disturbance in the Flow", message)
        self.initiate_chaos_button.setEnabled(True)
        self.initiate_chaos_button.setText("Initiate Working")
        self.chaos_thread = None
        self.chaos_worker = None

    def pan_fractal_view(self, pixel_delta):
        if self.is_animating_fractal: elapsed_time=time.time()-self.animation_start_time; time_cycle=(elapsed_time%ANIMATION_DURATION_SEC)/ANIMATION_DURATION_SEC; sin_wave=math.sin(time_cycle*2.0*math.pi); current_re_span=self.base_view_params['re_span']*(1.0-(ANIMATION_ZOOM_MAGNITUDE*sin_wave))
        else: current_re_span=self.base_view_params['re_span']
        width,height=self.fractal_display.width(),self.fractal_display.height();
        if width<=0 or height<=0: return
        aspect_ratio=width/height; current_im_span=current_re_span/aspect_ratio; re_offset=(pixel_delta.x()/width)*current_re_span; im_offset=(pixel_delta.y()/height)*current_im_span
        self.base_view_params['re_center']-=re_offset; self.base_view_params['im_center']-=im_offset
        self.trigger_full_regeneration_from_state(False)

    def zoom_fractal_view(self, angle_delta, mouse_pos_qpointf):
        zoom_factor = 1.15 if angle_delta > 0 else 1 / 1.15
        width, height = self.fractal_display.width(), self.fractal_display.height()
        if width <=0 or height <= 0: return
        re_span = self.base_view_params['re_span']; im_span = re_span / (width / height)
        mouse_pos = QPointF(mouse_pos_qpointf.x(), mouse_pos_qpointf.y())
        mouse_re = self.base_view_params['re_center'] - (re_span / 2) + (mouse_pos.x() / width) * re_span
        mouse_im = self.base_view_params['im_center'] - (im_span / 2) + (mouse_pos.y() / height) * im_span
        self.base_view_params['re_center'] = mouse_re + (self.base_view_params['re_center'] - mouse_re) / zoom_factor
        self.base_view_params['im_center'] = mouse_im + (self.base_view_params['im_center'] - mouse_im) / zoom_factor
        self.base_view_params['re_span'] /= zoom_factor
        self.trigger_full_regeneration_from_state(False)

    @Slot()
    def toggle_effects(self):
        current_states = {
            'strobe': self.effect_strobe_checkbox.isChecked(), 'colors': self.effect_colors_checkbox.isChecked(), 'bands': self.effect_bands_checkbox.isChecked(),
            'scan': self.effect_scan_lines_checkbox.isChecked(), 'neon': self.effect_neon_edges_checkbox.isChecked(),
            'emboss': self.effect_emboss_checkbox.isChecked(), 'rgb': self.effect_rgb_shift_checkbox.isChecked(),
            'crush': self.effect_color_crush_checkbox.isChecked(), 'glitch': self.effect_pixel_glitch_checkbox.isChecked(),
            'morph': self.effect_morph_checkbox.isChecked(),
        }
        for name, is_checked in current_states.items():
            if is_checked and not self.previous_effect_states[name]: self._randomize_effect_parameters(name)
        self.previous_effect_states = current_states

        self.effect_states.update(current_states)

        if self.effect_states['colors']: self.effect_strobe_checkbox.setChecked(False); self.effect_states['strobe'] = False

        self.trigger_full_regeneration_from_state(False)

    def update_animated_fractal_structure(self):
        if not self.is_animating_fractal: return
        if self.effect_states['strobe'] and not self.effect_states['colors']: self.palette_id_counter += 1
        elapsed_time=time.time()-self.animation_start_time; self.current_time_phase=(elapsed_time%ANIMATION_DURATION_SEC)/ANIMATION_DURATION_SEC; sin_wave=math.sin(self.current_time_phase*2.0*math.pi)
        current_re_span=self.base_view_params['re_span']*(1.0-(ANIMATION_ZOOM_MAGNITUDE*sin_wave)); display_aspect=self.fractal_display.width()/max(1,self.fractal_display.height())
        pan_offset_x=ANIMATION_PAN_MAGNITUDE_X*current_re_span*math.cos(self.current_time_phase*2.0*math.pi); pan_offset_y=ANIMATION_PAN_MAGNITUDE_Y*(current_re_span/display_aspect)*sin_wave
        current_re_center=self.base_view_params['re_center']+pan_offset_x; current_im_center=self.base_view_params['im_center']+pan_offset_y
        anim_params={'re_span': current_re_span, 're_center': current_re_center, 'im_center': current_im_center}
        self.regenerate_fractal_at_specific_params(anim_params, self.base_max_iter, self.julia_c_params if self.current_fractal_type == "Julia" else None)

    def regenerate_fractal_at_specific_params(self, view_params, max_iter, julia_c_tuple=None):
        dw, dh = self.fractal_display.width(), self.fractal_display.height(); rw = max(50, int(dw/self.render_scale_factor)); rh = max(50, int(dh/self.render_scale_factor))
        aspect_ratio = rw/rh if rh > 0 else 1.0; re_span = view_params['re_span']; re_center = view_params['re_center']; im_center = view_params['im_center']
        im_span = re_span/aspect_ratio; re_start, re_end = re_center-(re_span/2), re_center+(re_span/2); im_start, im_end = im_center-(im_span/2), im_center+(im_span/2)
        if self.iteration_data_np is None or self.iteration_data_np.shape != (rh, rw): self.iteration_data_np = np.empty((rh, rw), dtype=np.int32)
        if self.image_data_buffer_np is None or self.image_data_buffer_np.shape != (rh, rw, 3): self.image_data_buffer_np = np.empty((rh, rw, 3), dtype=np.uint8)
        self.current_max_iter_anim = max_iter

        if self.current_fractal_type == "Julia":
            jc_base = julia_c_tuple if julia_c_tuple and julia_c_tuple[0] is not None else (0.0,0.0); effective_jc = jc_base
            if self.effect_states['morph']:
                morph_angle = self.current_time_phase*2.0*math.pi*0.5; effective_jc = (jc_base[0]+self.julia_morph_radius*math.cos(morph_angle), jc_base[1]+self.julia_morph_radius*math.sin(morph_angle))
            calculate_julia_iterations_numba(self.iteration_data_np, re_start, re_end, im_start, im_end, rw, rh, max_iter, effective_jc[0], effective_jc[1])
        elif self.current_fractal_type == "Burning Ship": calculate_burning_ship_iterations_numba(self.iteration_data_np, re_start, re_end, im_start, im_end, rw, rh, max_iter)
        else: calculate_mandelbrot_iterations_numba(self.iteration_data_np, re_start, re_end, im_start, im_end, rw, rh, max_iter)

        if self.effect_states['neon']:
            if self.edge_data_np is None or self.edge_data_np.shape != self.iteration_data_np.shape: self.edge_data_np = np.zeros_like(self.iteration_data_np, dtype=np.float32)
            self.coloring_data_source = apply_sobel_filter(self.iteration_data_np, self.edge_data_np)
        elif self.effect_states['emboss']:
            if self.edge_data_np is None or self.edge_data_np.shape != self.iteration_data_np.shape: self.edge_data_np = np.zeros_like(self.iteration_data_np, dtype=np.float32)
            self.coloring_data_source = apply_emboss_filter(self.iteration_data_np, self.edge_data_np)
        else: self.coloring_data_source = self.iteration_data_np
        self.apply_new_palette_and_render()

    def apply_new_palette_and_render(self):
        if self.coloring_data_source is None or self.image_data_buffer_np is None: return
        if self.effect_states['strobe'] and not self.effect_states['colors'] and not self.is_animating_fractal: self.palette_id_counter += 1

        rand_params = (self.psych_params, self.warping_bands_freq, self.warping_bands_amp, self.tunnel_power, self.pixel_glitch_chance, self.color_crush_levels, self.palette_params, self.scan_line_spacing, self.scan_line_darkness)
        effects_tuple = (self.effect_states['colors'], self.effect_states['bands'], self.effect_states['tunnel'], self.effect_states['glitch'], self.effect_states['crush'], self.effect_states['scan'], self.current_time_phase, rand_params)

        apply_colors_to_iteration_data_numba(self.coloring_data_source, self.image_data_buffer_np, self.current_max_iter_anim, self.palette_id_counter, effects_tuple)
        h, w, ch = self.image_data_buffer_np.shape; bytes_per_line = w * ch
        if not self.image_data_buffer_np.flags['C_CONTIGUOUS']: self.image_data_buffer_np = np.ascontiguousarray(self.image_data_buffer_np)
        q_img = QImage(self.image_data_buffer_np.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.fractal_display.update_fractal_pixmap(QPixmap.fromImage(q_img.copy()))

    @Slot()
    def import_sigil(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Sigil Image", "", "Image Files (*.png *.jpg *.jpeg *.gif)");
        if not file_path: print("Sigil import cancelled."); return
        loaded_pixmap = QPixmap(file_path);
        if loaded_pixmap.isNull(): print(f"Failed to load sigil image: {file_path}"); self.remove_sigil()
        else:
            print(f"Sigil loaded: {file_path}"); self.sigil_original_pixmap = loaded_pixmap; self.sigil_current_scale_percent = INITIAL_SIGIL_SCALE_PERCENT; self.sigil_scale_input.setText(str(int(self.sigil_current_scale_percent)))
            max_initial_dim = 150; initial_display_size = self.sigil_original_pixmap.size()
            if initial_display_size.width() > max_initial_dim or initial_display_size.height() > max_initial_dim: initial_display_size = initial_display_size.scaled(max_initial_dim, max_initial_dim, Qt.AspectRatioMode.KeepAspectRatio)
            self.fractal_display.set_sigil_parameters(self.sigil_original_pixmap, initial_display_size, True)
            self.remove_sigil_button.setEnabled(True); self.sigil_scale_input.setEnabled(True); self.apply_sigil_scale_button.setEnabled(True)
            self.update_sigil_flash_position(); self.sigil_flash_timer.start(SIGIL_FLASH_INTERVAL_MS)
    @Slot()
    def remove_sigil(self):
        print("Removing sigil."); self.sigil_original_pixmap = None; self.fractal_display.set_sigil_parameters(None, QSize(0,0), False); self.sigil_flash_timer.stop()
        self.remove_sigil_button.setEnabled(False); self.sigil_scale_input.setEnabled(False); self.apply_sigil_scale_button.setEnabled(False); self.sigil_scale_input.setText(str(int(INITIAL_SIGIL_SCALE_PERCENT)))
    @Slot()
    def apply_sigil_scale(self):
        if not self.sigil_original_pixmap: print("No sigil to scale."); return
        try:
            scale_percent = float(self.sigil_scale_input.text()); scale_percent = max(1.0, min(500.0, scale_percent)); self.sigil_current_scale_percent = scale_percent; self.sigil_scale_input.setText(str(int(scale_percent)))
            initial_size = self.fractal_display.sigil_initial_display_size
            new_w = int(initial_size.width() * (scale_percent/100.0)); new_h = int(initial_size.height() * (scale_percent/100.0))
            self.fractal_display.update_sigil_target_size(QSize(max(10, new_w), max(10, new_h))); print(f"Sigil scaled to {scale_percent}%, target size: {new_w}x{new_h}")
        except ValueError: print("Invalid sigil scale value."); self.sigil_scale_input.setText(str(int(self.sigil_current_scale_percent)))
    @Slot()
    def update_sigil_flash_position(self):
        if self.fractal_display.sigil_visible and self.fractal_display.sigil_original_pixmap:
            disp_w=self.fractal_display.width(); disp_h=self.fractal_display.height(); sigil_w=self.fractal_display.sigil_target_display_size.width(); sigil_h=self.fractal_display.sigil_target_display_size.height()
            if disp_w>sigil_w and disp_h>sigil_h: self.fractal_display.update_sigil_position(QPoint(random.randint(0,disp_w-sigil_w),random.randint(0,disp_h-sigil_h)))
            else: self.fractal_display.update_sigil_position(QPoint(0,0))
    @Slot()
    def save_fractal_image(self):
        print("Preparing to save fractal image..."); was_animating = self.is_animating_fractal;
        if was_animating: self.animation_timer.stop()
        save_w, save_h = 1920, 1080; aspect_ratio = save_w / save_h; params = self.base_view_params; max_iter = self.base_max_iter * 2; julia_params = self.julia_c_params if self.current_fractal_type == "Julia" else None; re_span = params['re_span']; im_span = re_span / aspect_ratio; re_start, re_end = params['re_center']-(re_span/2), params['re_center']+(re_span/2); im_start, im_end = params['im_center']-(im_span/2), params['im_center']+(im_span/2)
        iter_data_save = np.empty((save_h, save_w), dtype=np.int32); img_buffer_save = np.empty((save_h, save_w, 3), dtype=np.uint8); print(f"  Saving base {self.current_fractal_type} ({save_w}x{save_h}, iter={max_iter})...")
        if self.current_fractal_type == "Julia": jc = julia_params if julia_params and julia_params[0] is not None else (0.0,0.0); calculate_julia_iterations_numba(iter_data_save, re_start, re_end, im_start, im_end, save_w, save_h, max_iter, jc[0], jc[1])
        elif self.current_fractal_type == "Burning Ship": calculate_burning_ship_iterations_numba(iter_data_save, re_start, re_end, im_start, im_end, save_w, save_h, max_iter)
        else: calculate_mandelbrot_iterations_numba(iter_data_save, re_start, re_end, im_start, im_end, save_w, save_h, max_iter)
        rand_params = (self.psych_params, self.warping_bands_freq, self.warping_bands_amp, self.tunnel_power, self.pixel_glitch_chance, self.color_crush_levels, (random.uniform(5,20), random.uniform(2,10), random.uniform(1,5)), self.scan_line_spacing, self.scan_line_darkness)
        apply_colors_to_iteration_data_numba(iter_data_save, img_buffer_save, max_iter, random.randint(0, 3), (False, False, False, False, False, False, 0, rand_params)); save_image = QImage(img_buffer_save.data, save_w, save_h, save_w * 3, QImage.Format.Format_RGB888).copy()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Fractal", f"{self.current_fractal_type}_fractal.png", "PNG (*.png);;JPEG (*.jpg *.jpeg)");
        if file_path:
            if save_image.save(file_path): print(f"Successfully saved image to: {file_path}")
            else: print(f"Failed to save image to: {file_path}")
        else: print("Save cancelled.")
        if was_animating: self.animation_timer.start(ANIMATION_INTERVAL_MS)
    @Slot(str)
    def on_fractal_type_changed(self, type_text):
        self.current_fractal_type = type_text; self.julia_c_widget.setVisible(type_text == "Julia")
        self.effect_morph_checkbox.setEnabled(type_text == "Julia")
        if type_text != "Julia" and self.effect_states['morph']: self.effect_morph_checkbox.setChecked(False)
        self.trigger_full_regeneration_from_intent()
    def toggle_fractal_animation(self, state):
        self.is_animating_fractal = (state == Qt.CheckState.Checked.value); print(f"Fractal animation {'ENABLED' if self.is_animating_fractal else 'DISABLED'}.")
        self.trigger_full_regeneration_from_state(False)
    def apply_performance_settings(self):
        print("Applying settings..."); scale_changed, iter_changed = False, False; global DEFAULT_MAX_ITER_BASE
        try:
            new_scale = float(self.scale_input.text()); new_scale = max(0.5, min(10.0, new_scale))
            if abs(self.render_scale_factor-new_scale) > 1e-5: self.render_scale_factor=new_scale; scale_changed=True
            self.scale_input.setText(str(self.render_scale_factor)); print(f"  Render scale factor set to: {self.render_scale_factor}")
        except ValueError: print("  Invalid input for render scale factor."); self.scale_input.setText(str(self.render_scale_factor))
        try:
            new_base_iter = int(self.max_iter_input.text()); new_base_iter = max(10, min(1000, new_base_iter))
            if DEFAULT_MAX_ITER_BASE != new_base_iter: DEFAULT_MAX_ITER_BASE = new_base_iter; iter_changed=True
            self.max_iter_input.setText(str(DEFAULT_MAX_ITER_BASE)); print(f"  Global base max iterations set to: {DEFAULT_MAX_ITER_BASE}")
        except ValueError: print("  Invalid input for base max iterations."); self.max_iter_input.setText(str(DEFAULT_MAX_ITER_BASE))
        if scale_changed or iter_changed: self.trigger_full_regeneration_from_intent(reset_animation_time=False)
        else: print("  No valid changes applied.")
    def trigger_full_regeneration_from_intent(self, reset_animation_time=True):
        print(f"Generating NEW BASE ({self.current_fractal_type}) from intent..."); intent_str = self.intent_input.text()
        if not intent_str or intent_str == self.initial_intent_string: intent_str = f"{self.current_fractal_type} Default"
        display_w=self.fractal_display.width(); display_h=self.fractal_display.height(); rw=max(50, int(display_w/self.render_scale_factor)); rh=max(50, int(display_h/self.render_scale_factor)); asp=rw/rh if rh > 0 else 1.0
        base_re_s, base_re_c, base_im_c, base_max_i, jc_r, jc_i = generate_fractal_view_params(intent_str, asp, self.current_fractal_type)
        self.base_view_params = {'re_span': base_re_s, 're_center': base_re_c, 'im_center': base_im_c}; self.base_max_iter = base_max_i
        if self.current_fractal_type == "Julia":
            try: ui_jc_r = float(self.julia_c_real_input.text()); ui_jc_i = float(self.julia_c_imag_input.text()); self.julia_c_params = (ui_jc_r, ui_jc_i)
            except ValueError: self.julia_c_params = (jc_r, jc_i) if jc_r is not None else (0.0,0.0); self.julia_c_real_input.setText(f"{self.julia_c_params[0]:.4f}"); self.julia_c_imag_input.setText(f"{self.julia_c_params[1]:.4f}")
        else: self.julia_c_params = (None, None)
        self.trigger_full_regeneration_from_state(reset_animation_time)
    def trigger_full_regeneration_from_state(self, reset_animation_time=True):
        self.animation_timer.stop(); self.strobe_timer.stop()
        if reset_animation_time: self.animation_start_time = time.time(); self.current_time_phase = 0.0
        cjc = self.julia_c_params if self.current_fractal_type == "Julia" else None
        if self.is_animating_fractal: self.animation_timer.start(ANIMATION_INTERVAL_MS); self.update_animated_fractal_structure()
        else:
            if self.effect_states['strobe']: self.strobe_timer.start(STROBE_INTERVAL_MS)
            self.regenerate_fractal_at_specific_params(self.base_view_params, self.base_max_iter, cjc)
    _resize_debounce_timer = None
    def resizeEvent(self, event):
        super().resizeEvent(event);
        if self._resize_debounce_timer and self._resize_debounce_timer.isActive(): self._resize_debounce_timer.stop()
        self._resize_debounce_timer = QTimer(); self._resize_debounce_timer.setSingleShot(True); self._resize_debounce_timer.timeout.connect(self.handle_debounced_resize); self._resize_debounce_timer.start(500)
    def handle_debounced_resize(self): print("Handling debounced resize - regenerating fractal structure."); self.trigger_full_regeneration_from_state(reset_animation_time=False)
    def _tone_callback(self, outdata, frames, time_info, status):
        if status: print(status, file=sys.stderr)
        t = (self._tone_data_pos + np.arange(frames)) / SAMPLE_RATE; t = t.reshape(-1, 1); wave_data = self.tone_volume * np.sin(2 * np.pi * self.current_tone_frequency * t); outdata[:] = wave_data.astype(np.float32); self._tone_data_pos += frames
    @Slot()
    def update_tone_frequency(self):
        if not SOUNDDEVICE_AVAILABLE: return
        try:
            freq = float(self.tone_freq_input.text());
            if freq <= 0: print("Frequency must be positive."); self.tone_freq_input.setText(str(self.current_tone_frequency)); return
            if self.current_tone_frequency != freq: self.current_tone_frequency = freq; print(f"Tone frequency set to: {freq} Hz")
        except ValueError: print("Invalid frequency input."); self.tone_freq_input.setText(str(self.current_tone_frequency))
    @Slot()
    def play_frequency_tone(self):
        if not SOUNDDEVICE_AVAILABLE: return
        self.update_tone_frequency();
        if self.is_tone_playing: self.stop_frequency_tone()
        try:
            self._tone_data_pos = 0; self.tone_stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, callback=self._tone_callback, dtype='float32'); self.tone_stream.start()
            self.is_tone_playing = True; self.stop_tone_button.setEnabled(True); self.play_tone_button.setEnabled(False); print(f"Playing tone: {self.current_tone_frequency} Hz")
        except Exception as e: print(f"Error starting tone: {e}"); self.stop_frequency_tone()
    @Slot()
    def stop_frequency_tone(self):
        if not SOUNDDEVICE_AVAILABLE or not self.is_tone_playing: return
        if self.tone_stream:
            try: self.tone_stream.stop(); self.tone_stream.close()
            except Exception as e: print(f"Error stopping tone stream: {e}")
            self.tone_stream = None
        self.is_tone_playing = False; self.stop_tone_button.setEnabled(False); self.play_tone_button.setEnabled(True); print("Tone stopped.")
    @Slot(int)
    def set_tone_volume(self, value): self.tone_volume = value / 100.0;
    @Slot()
    def upload_music_track(self):
        if not PYGAME_AVAILABLE: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Music Track", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file_path:
            self.uploaded_track_path = file_path
            for i in range(self.music_track_combo.count()):
                if self.music_track_combo.itemText(i).startswith("Uploaded:"): self.music_track_combo.removeItem(i); break
            file_name = os.path.basename(file_path); self.music_track_combo.addItem(f"Uploaded: {file_name}"); self.music_track_combo.setCurrentText(f"Uploaded: {file_name}"); print(f"Uploaded new track: {file_path}"); self.play_selected_music()
    @Slot()
    def toggle_play_pause_music(self):
        if not PYGAME_AVAILABLE: return
        if pygame.mixer.music.get_busy():
            if self.is_music_paused: pygame.mixer.music.unpause(); self.is_music_paused = False; print("Resuming music.")
            else: pygame.mixer.music.pause(); self.is_music_paused = True; print("Pausing music.")
        else: self.play_selected_music()
        self.update_music_button_state()
    def play_selected_music(self):
        if not PYGAME_AVAILABLE: return
        selected_text = self.music_track_combo.currentText(); source_path = None
        if selected_text.startswith("Uploaded:"): source_path = self.uploaded_track_path
        elif selected_text in self.predefined_tracks: source_path = self.predefined_tracks[selected_text]
        if source_path and os.path.exists(source_path):
            try: pygame.mixer.music.load(source_path); pygame.mixer.music.play(); self.is_music_paused = False; print(f"Playing: {source_path}")
            except pygame.error as e: print(f"Error playing music file '{source_path}': {e}")
        else: print(f"Error: Music file not found or not selected: {source_path}")
        self.update_music_button_state()
    @Slot(int)
    def set_music_volume(self, value):
        if not PYGAME_AVAILABLE: return; pygame.mixer.music.set_volume(value / 100.0)
    @Slot()
    def update_music_button_state(self):
        # FIX: Add guard clause to prevent crash if mixer is not initialized
        if not PYGAME_AVAILABLE or not pygame.get_init() or not pygame.mixer.get_init():
            return
        if pygame.mixer.music.get_busy():
            self.play_pause_music_button.setText("Pause") if not self.is_music_paused else self.play_pause_music_button.setText("Resume")
        else:
            self.play_pause_music_button.setText("Play")
            self.is_music_paused = False
    def closeEvent(self, event):
        if self.chaos_thread and self.chaos_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirm Close',
                                       "A 'Working' is in progress. Are you sure you want to quit?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        print("Closing application, stopping all audio..."); self.stop_frequency_tone();
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
                pygame.quit()
            except pygame.error:
                # Ignore errors if pygame is already uninitialized
                pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 8)) # Use a smaller default font for compactness
    window = MainWindow()
    window.show()
    sys.exit(app.exec())