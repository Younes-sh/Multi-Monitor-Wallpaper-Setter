import sys
import os
import subprocess
import tempfile
import shutil
import uuid


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea
)


class MonitorRow(QWidget):
    def __init__(self, index, screen):
        super().__init__()
        self.index = index
        self.screen = screen
        self.image_path = ""

        geo = screen.geometry()
        info_text = (
            f"Monitor {index + 1}: {screen.name()}  "
            f"({geo.width()}x{geo.height()} @ {geo.x()},{geo.y()})"
        )

        layout = QHBoxLayout()
        self.info_label = QLabel(info_text)
        self.info_label.setMinimumWidth(260)

        self.btn_select = QPushButton("Select Image")
        self.btn_select.clicked.connect(self.select_image)

        self.file_label = QLabel("No image selected")

        layout.addWidget(self.info_label)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.file_label)
        self.setLayout(layout)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Image for Monitor {self.index + 1}", "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.image_path = os.path.normpath(file_path)
            self.file_label.setText(os.path.basename(file_path))


class WallpaperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Multi-Monitor Wallpaper Setter")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setMinimumWidth(600)

        main_layout = QVBoxLayout()

        screens = QApplication.screens()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        rows_layout = QVBoxLayout()

        for i, screen in enumerate(screens):
            row = MonitorRow(i, screen)
            self.rows.append(row)
            rows_layout.addWidget(row)

        container.setLayout(rows_layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.btn_apply = QPushButton("Apply Wallpapers")
        self.btn_apply.setStyleSheet(
            "font-weight: bold; background-color: #0078D4; color: white; padding: 8px;"
        )
        self.btn_apply.clicked.connect(self.apply_wallpapers)
        main_layout.addWidget(self.btn_apply)

        self.footer_label = QLabel("Developed by UP — ultrapixel.app")
        self.footer_label.setStyleSheet("color: gray; font-size: 11px;")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.footer_label)

        self.setLayout(main_layout)

    def apply_wallpapers(self):
        selections = [row.image_path for row in self.rows]

        if not any(selections):
            QMessageBox.warning(
                self, "Error", "Please select an image for at least one monitor."
            )
            return

        try:
            monitor_calls = []
            self._temp_files = []
            for i, path in enumerate(selections):
                if path:
                    ext = os.path.splitext(path)[1]
                    temp_img = os.path.join(
                        tempfile.gettempdir(), f"wallpaper_{i}_{uuid.uuid4().hex}{ext}"
                    )
                    shutil.copy2(path, temp_img)
                    self._temp_files.append(temp_img)
                    escaped = temp_img.replace("'", "''")
                    geo = self.rows[i].screen.geometry()
                    monitor_calls.append(
                        f"""
        if (r.Left == {geo.x()} && r.Top == {geo.y()}) {{
            dw.SetWallpaper(id, @"{escaped}");
        }}"""
                    )
            monitor_calls_code = "".join(monitor_calls)

            ps_code = f"""
$code = @"
using System;
using System.Runtime.InteropServices;
using System.Threading;

[StructLayout(LayoutKind.Sequential)]
public struct RECT {{
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}}

public enum DesktopWallpaperPosition {{
    Center = 0, Tile = 1, Stretch = 2, Fit = 3, Fill = 4, Span = 5
}}

public enum DesktopSlideshowDirection {{ Forward = 0, Backward = 1 }}
public enum DesktopSlideshowOptions {{ ShuffleImages = 0x01 }}

[ComImport]
[Guid("B92B56A9-8B55-4E14-9A89-0199BBB6F93B")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IDesktopWallpaper {{
    void SetWallpaper([MarshalAs(UnmanagedType.LPWStr)] string monitorID, [MarshalAs(UnmanagedType.LPWStr)] string wallpaper);
    [return: MarshalAs(UnmanagedType.LPWStr)] string GetWallpaper([MarshalAs(UnmanagedType.LPWStr)] string monitorID);
    [return: MarshalAs(UnmanagedType.LPWStr)] string GetMonitorDevicePathAt(uint monitorIndex);
    uint GetMonitorDevicePathCount();
    RECT GetMonitorRECT([MarshalAs(UnmanagedType.LPWStr)] string monitorID);
    void SetBackgroundColor(uint color);
    uint GetBackgroundColor();
    void SetPosition(DesktopWallpaperPosition position);
    DesktopWallpaperPosition GetPosition();
    void SetSlideshow(IntPtr items);
    IntPtr GetSlideshow();
    void SetSlideshowOptions(DesktopSlideshowOptions options, uint slideshowTick);
    void GetSlideshowOptions(out DesktopSlideshowOptions options, out uint slideshowTick);
    void AdvanceSlideshow([MarshalAs(UnmanagedType.LPWStr)] string monitorID, DesktopSlideshowDirection direction);
    int GetStatus();
    bool Enable();
}}

[ComImport]
[Guid("C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD")]
public class DesktopWallpaperClass {{ }}

public class Wallpaper {{
    static bool success = true;
    static string errorMessage = "";

    static void ApplyOnStaThread() {{
        try {{
            IDesktopWallpaper dw = (IDesktopWallpaper)new DesktopWallpaperClass();
            dw.SetPosition(DesktopWallpaperPosition.Fill);
            uint count = dw.GetMonitorDevicePathCount();
            for (uint idx = 0; idx < count; idx++) {{
                string id = dw.GetMonitorDevicePathAt(idx);
                RECT r = dw.GetMonitorRECT(id);
{monitor_calls_code}
            }}
        }} catch (Exception ex) {{
            success = false;
            errorMessage = ex.Message;
        }}
    }}

    public static void Apply() {{
        Thread th = new Thread(ApplyOnStaThread);
        th.SetApartmentState(ApartmentState.STA);
        th.Start();
        th.Join();
        if (!success) {{
            throw new Exception(errorMessage);
        }}
    }}
}}
"@
Add-Type -TypeDefinition $code
[Wallpaper]::Apply()
"""

            temp_dir = tempfile.gettempdir()
            script_path = os.path.join(temp_dir, "set_wallpaper.ps1")

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(ps_code)

            cmd = ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-File", script_path]
            process = subprocess.run(
                cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            if os.path.exists(script_path):
                os.remove(script_path)

            if process.returncode == 0:
                QMessageBox.information(self, "Success", "Wallpapers applied successfully!")
            else:
                QMessageBox.critical(self, "Error", f"Script execution failed:\n{process.stderr}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")


if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes
        myappid = "UP.UltraPixel.DualMonitorWallpaperSetter.1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    window = WallpaperApp()
    window.show()
    sys.exit(app.exec())