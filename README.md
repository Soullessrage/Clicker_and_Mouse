# Neon Mouse Controller

A desktop mouse auto-clicker and path follower with a neon-themed Tkinter interface. The app starts only when activated from its UI or a hotkey, and stops its active action when it detects manual mouse movement.

## Download and install

1. On GitHub, select **Code** → **Download ZIP**.
2. Extract the ZIP file. Open a terminal (PowerShell on Windows) in the extracted `Clicker_and_Mouse` folder, the one containing this README and `requirements.txt`.
3. Install Python 3.10 or later if it is not already installed.
4. Create and activate a virtual environment, then install the dependency:

**Windows PowerShell**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

**macOS or Linux**

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Linux, install your distribution's Tkinter package if Python reports that `tkinter` is missing (for example, `sudo apt install python3-tk` on Ubuntu/Debian).

## Run

From the extracted project folder, with the virtual environment activated:

**Windows PowerShell**

```powershell
python mouse_controller\main.py
```

**macOS or Linux**

```sh
./run_mouse_controller
```

Alternatively, run `python3 mouse_controller/main.py` on macOS or Linux. Keep the app in a graphical desktop session; a headless terminal or server does not provide the display needed by Tkinter and `pynput`. On macOS, grant Accessibility/Input Monitoring permission to the terminal or Python process if prompted. Linux desktop support depends on the session; `pynput` generally works best under X11, while Wayland may restrict global input control.

## Use

- Toggle **Auto Clicker** to start or stop clicking; adjust clicks per second with its slider.
- Choose **Circle**, **Square**, or **Triangle** to start following that path around the current pointer position.
- Draw a stroke on the canvas and select **Use Drawn Path** to follow it. Adjust movement speed with the path slider.
- Press **Ctrl+Alt+A** to toggle the clicker, **Ctrl+Alt+P** to toggle path following, or **Ctrl+Alt+S** to stop all activity.
- Moving the mouse manually disengages the active action. Reactivate it from the UI or a hotkey.

The two movement modes cannot run at the same time. Use the **Stop All** button or the stop hotkey whenever you need to halt activity immediately.
