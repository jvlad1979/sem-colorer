from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QColorDialog,
                           QLabel, QSpinBox, QDoubleSpinBox, QTabWidget, QTextEdit,
                           QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QColorDialog,
                           QLabel, QSpinBox, QDoubleSpinBox, QTabWidget, QTextEdit,
                           QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtSvg import QSvgRenderer  # Add this import
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
import sys
import json
from pathlib import Path
from .core import svg_gate_colorer, get_svg_gates
import tempfile
from cairosvg import svg2png
import subprocess
from PyQt6.QtGui import QImage

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QColorDialog,
                           QLabel, QSpinBox, QDoubleSpinBox, QTabWidget, QTextEdit,
                           QScrollArea, QComboBox, QGridLayout)
from matplotlib.pyplot import colormaps
# ... existing imports ...

class GateColorWidget(QWidget):
    def __init__(self, gate_name, parent=None):
        super().__init__(parent)
        self.gate_name = gate_name
        layout = QHBoxLayout()
        
        # Gate name label
        layout.addWidget(QLabel(gate_name))
        
        # Value slider
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(0, 1)
        self.value_spin.setValue(0.5)
        self.value_spin.setSingleStep(0.1)
        layout.addWidget(self.value_spin)
        
        # Color picker
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.clicked.connect(self.pick_color)
        self.set_button_color("#000000")
        layout.addWidget(self.color_btn)
        
        # Opacity slider
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0, 1)
        self.opacity_spin.setValue(0.7)
        self.opacity_spin.setSingleStep(0.1)
        layout.addWidget(self.opacity_spin)
        
        self.setLayout(layout)
        
    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_button_color(color.name())
            
    def set_button_color(self, color):
        self.color_btn.setStyleSheet(f"background-color: {color};")
        
    def get_value(self):
        return {
            "value": self.color_btn.palette().button().color().name() 
                    if self.color_btn.styleSheet() 
                    else self.value_spin.value(),
            "opacity": self.opacity_spin.value()
        }

class ColorEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        
        # Initialize timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_preview)
        
        # Colormap selection
        cmap_layout = QHBoxLayout()
        cmap_layout.addWidget(QLabel("Colormap:"))
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(sorted(colormaps()))
        self.cmap_combo.setCurrentText("viridis")
        self.cmap_combo.currentTextChanged.connect(self.schedule_update)
        cmap_layout.addWidget(self.cmap_combo)
        
        # Range controls
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Range:"))
        self.range_min = QDoubleSpinBox()
        self.range_min.setRange(0, 1)
        self.range_min.setValue(0)
        self.range_min.valueChanged.connect(self.schedule_update)
        range_layout.addWidget(self.range_min)
        self.range_max = QDoubleSpinBox()
        self.range_max.setRange(0, 1)
        self.range_max.setValue(1)
        self.range_max.valueChanged.connect(self.schedule_update)
        range_layout.addWidget(self.range_max)
        
        # Gate colors area
        self.gates_widget = QWidget()
        self.gates_layout = QVBoxLayout()
        self.gates_widget.setLayout(self.gates_layout)
        
        # Scroll area for gates
        scroll = QScrollArea()
        scroll.setWidget(self.gates_widget)
        scroll.setWidgetResizable(True)
        
        # Layout setup
        self.layout.addLayout(cmap_layout)
        self.layout.addLayout(range_layout)
        self.layout.addWidget(scroll)
        self.setLayout(self.layout)
        
        self.gate_widgets = {}

    def set_default_json(self, gates: list[str]):
        """Update controls with gate list"""
        # Clear existing gates
        for widget in self.gate_widgets.values():
            widget.deleteLater()
        self.gate_widgets.clear()
        
        # Add new gates
        for gate in gates:
            widget = GateColorWidget(gate, self)
            self.gates_layout.addWidget(widget)
            self.gate_widgets[gate] = widget
            widget.value_spin.valueChanged.connect(self.schedule_update)
            widget.opacity_spin.valueChanged.connect(self.schedule_update)
            
    def get_current_spec(self):
        """Get current color specification from widgets"""
        return {
            "colormap": self.cmap_combo.currentText(),
            "norm_range": [self.range_min.value(), self.range_max.value()],
            "gate_colors": {
                gate: widget.get_value()
                for gate, widget in self.gate_widgets.items()
            }
        }

    def schedule_update(self):
        self.update_timer.start(500)
        
    def update_preview(self):
        if isinstance(self.parent(), MainWindow):
            self.parent().update_preview(self.get_current_spec())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SEM Colorer")
        self.setMinimumSize(800, 600)
        
        self.statusBar()
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Left panel (controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.svg_label = QLabel("No file selected")

        # File selection
        file_buttons_layout = QHBoxLayout()
        self.select_svg_btn = QPushButton("Select SVG")
        self.select_svg_btn.clicked.connect(self.select_svg)
        self.refresh_btn = QPushButton("Refresh Preview")
        self.refresh_btn.clicked.connect(lambda: self.update_preview())
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_preview)
        file_buttons_layout.addWidget(self.select_svg_btn)
        file_buttons_layout.addWidget(self.refresh_btn)
        file_buttons_layout.addWidget(self.save_btn)
        
        # Opacity control
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Default Opacity:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0, 1)
        self.opacity_spin.setValue(0.5)
        self.opacity_spin.setSingleStep(0.1)
        opacity_layout.addWidget(self.opacity_spin)
        
        # Color editor
        self.color_editor = ColorEditor(self)
        
        # Layout setup
        left_layout.addLayout(file_buttons_layout)
        left_layout.addWidget(self.svg_label)
        left_layout.addLayout(opacity_layout)
        left_layout.addWidget(self.color_editor)
        
        # Opacity control
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Default Opacity:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0, 1)
        self.opacity_spin.setValue(0.5)
        self.opacity_spin.setSingleStep(0.1)
        opacity_layout.addWidget(self.opacity_spin)
        
        # Color editor
        # self.color_editor = ColorEditor(self)
        
        # left_layout.addWidget(self.select_svg_btn)
        # left_layout.addWidget(self.svg_label)
        # left_layout.addLayout(opacity_layout)
        # left_layout.addWidget(self.color_editor)
        
        # Right panel (preview)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        scroll_area.setWidget(self.preview_label)
        
        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(scroll_area, stretch=2)
        
        self.svg_path = None
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Connect opacity spinner to preview update
        self.opacity_spin.valueChanged.connect(lambda: self.update_preview())
        
    def update_preview(self, spec=None):
        if not self.svg_path:
            return
            
        try:
            preview_path = Path(self.temp_dir.name) / "preview.svg"
            png_path = Path(self.temp_dir.name) / "preview.png"
            
            if spec is None:
                spec = self.color_editor.get_current_spec()
            
            svg_gate_colorer(
                svg_origin=self.svg_path,
                svg_target=preview_path,
                color_spec=spec,
                fill_opacity=self.opacity_spin.value()
            )
            
            if preview_path.exists():
                try:
                    # Get original SVG dimensions
                    renderer = QSvgRenderer(str(preview_path))
                    original_size = renderer.defaultSize()
                    if original_size.isEmpty():
                        original_size = QSize(800, 800)
                    aspect_ratio = original_size.width() / original_size.height()
                    
                    # Calculate size that fits in preview label while maintaining aspect ratio
                    label_size = self.preview_label.size()
                    label_aspect = label_size.width() / label_size.height()
                    
                    if label_aspect > aspect_ratio:
                        # Label is wider than needed
                        height = label_size.height()
                        width = int(height * aspect_ratio)
                    else:
                        # Label is taller than needed
                        width = label_size.width()
                        height = int(width / aspect_ratio)
                    
                    # Use Inkscape with calculated dimensions
                    subprocess.run([
                        'inkscape',
                        '--export-type=png',
                        f'--export-width={width}',
                        f'--export-height={height}',
                        '--export-background-opacity=0',
                        '--export-filename=' + str(png_path),
                        str(preview_path)
                    ], check=True, capture_output=True)
                    
                    # Load PNG directly without additional scaling
                    image = QImage(str(png_path))
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        self.preview_label.setPixmap(pixmap)
                        print(f"Successfully rendered SVG preview at {width}x{height}")
                    else:
                        print("Failed to load preview image")
                        
                except subprocess.CalledProcessError as e:
                    print(f"Inkscape rendering failed: {e}")
                    print(f"Inkscape stderr: {e.stderr.decode()}")
                    
        except Exception as e:
            print(f"Error updating preview: {str(e)}")
            self.svg_label.setText(f"Error: {str(e)}")
    
    def select_svg(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select SVG File",
            "",
            "SVG Files (*.svg)"
        )
        if file_name:
            self.svg_path = file_name
            self.svg_label.setText(Path(file_name).name)
            
            # Get gates from SVG and update JSON template
            gates = get_svg_gates(file_name)
            self.color_editor.set_default_json(gates)
            
            self.update_preview()
    def save_preview(self):
        if not self.svg_path:
            self.statusBar().showMessage("No SVG file loaded", 3000)
            return
                
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Preview",
            "",
            "SVG Files (*.svg);;PNG Files (*.png)"
        )
        
        if not file_name:
            return
            
        try:
            preview_path = Path(self.temp_dir.name) / "preview.svg"
            print(f"Preview path exists: {preview_path.exists()}")
            print(f"Saving to: {file_name}")
            
            if file_name.endswith('.svg'):
                # For SVG, just copy the preview file
                import shutil
                print(f"Copying from {preview_path} to {file_name}")
                shutil.copy2(str(preview_path), str(file_name))
                print("Copy completed")
                
            elif file_name.endswith('.png'):
                # For PNG, use Inkscape to convert with current preview dimensions
                label_size = self.preview_label.size()
                print(f"Converting to PNG with size {label_size.width()}x{label_size.height()}")
                result = subprocess.run([
                    'inkscape',
                    '--export-type=png',
                    f'--export-width={label_size.width()}',
                    f'--export-height={label_size.height()}',
                    '--export-background-opacity=0',
                    '--export-filename=' + str(file_name),
                    str(preview_path)
                ], check=True, capture_output=True, text=True)
                print(f"Inkscape output: {result.stdout}")
                
            # Verify the file was created
            output_path = Path(file_name)
            if output_path.exists():
                self.statusBar().showMessage(f"Saved to {file_name}", 3000)
                print(f"File successfully saved to {file_name}")
            else:
                raise FileNotFoundError(f"Output file {file_name} was not created")
                
        except Exception as e:
            error_msg = f"Error saving preview: {str(e)}"
            print(error_msg)
            if isinstance(e, subprocess.CalledProcessError):
                print(f"Inkscape stderr: {e.stderr}")
            self.statusBar().showMessage(error_msg, 5000)

    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()
def main():
    # Set the QT_QPA_PLATFORM environment variable to xcb
    import os
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())