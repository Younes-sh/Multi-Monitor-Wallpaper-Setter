# Multi-Monitor Wallpaper Setter

A simple Windows desktop application that automatically detects all connected
monitors and lets you set a **different wallpaper for each monitor
individually**.

Developed by **UP** — [ultrapixel.app](https://ultrapixel.app)

## Features

- Automatically detects all connected monitors (name, resolution, position)
- Lets you pick a separate image for each monitor
- Applies wallpapers using the native Windows `IDesktopWallpaper` COM API
- Correctly matches each image to the right physical monitor based on its
  actual screen position (not just enumeration order)
- Bypasses Windows' wallpaper path cache so repeated changes always apply
- Custom app icon shown both in the window and in the Windows taskbar

## Requirements

- Windows 10 / 11
- Python 3.10+
- PyQt6

Install dependencies:

```
pip install PyQt6 pyinstaller
```

## Running from source

```
python dual_wallpaper.py
```

## Building the Windows executable

Make sure `icon.ico` is in the project folder, then run:

```
pyinstaller dual_wallpaper.spec
```

The built executable will be created at:

```
dist/dual_wallpaper.exe
```

## Project structure

```
DESKTOP-BACKGROUND/
├── dual_wallpaper.py     # Main application
├── dual_wallpaper.spec   # PyInstaller build configuration
├── icon.ico              # Application icon (multi-size .ico)
└── README.md
```

## How it works

The app enumerates monitors via PyQt6 (`QApplication.screens()`) and, when
you click **Apply Wallpapers**, generates and runs a small PowerShell script
that calls the Windows `IDesktopWallpaper` COM interface on an STA thread.
Each selected image is first copied to a uniquely named temporary file to
avoid Windows' internal wallpaper cache, then matched to the correct monitor
by comparing its physical screen coordinates (not by list index, since the
COM API and PyQt6 do not always enumerate monitors in the same order).

## Platform support

This application currently supports **Windows only**. Wallpaper handling
relies on the Windows-specific `IDesktopWallpaper` COM API and PowerShell,
which have no equivalent on macOS or Linux.

## License

© UP — ultrapixel.app. All rights reserved.
