# Neon Mouse Controller

A desktop mouse auto-clicker and path follower with a neon-themed Tkinter interface. The app starts only when activated from its UI or a hotkey, and stops its active action when it detects manual mouse movement.

## Download and launch

1. On GitHub, select **Code** → **Download ZIP**, then extract the ZIP.
2. Make sure Python 3.10 or newer is installed. On Windows, use the standard installer from [python.org](https://www.python.org/downloads/) and include Tcl/Tk. On macOS or Linux, use a desktop Python installation that includes Tkinter.
3. Double-click the launcher for your computer:
   - **Windows:** `Run_Clicker.bat`
   - **macOS:** `Run_Clicker.command`
   - **Linux:** `Run_Clicker`

On first launch, the launcher creates a private `.venv` folder beside the app and installs its Python dependency. An internet connection is needed for this one-time setup. Later launches open the app directly. Keep the extracted folder in a location where your account can create files; the app stores its environment in `.venv` there.

To update an existing copy, click **Update & Restart** in the app. It downloads the latest files from the GitHub `main` branch, updates dependencies, and restarts the application. Keep an internet connection available and do not move or delete the extracted folder while updating.

If macOS asks for permission, allow Accessibility/Input Monitoring for the terminal or Python process. On Linux, Tkinter may need to be installed separately (for example, `sudo apt install python3-tk` on Ubuntu/Debian); global input control works best under X11 and may be restricted by Wayland. Run the launcher in a graphical desktop session, not a headless server.

## Use

- Toggle **Auto Clicker** to start or stop clicking; adjust clicks per second from 1 to 1000 with its slider. Operating-system scheduling and the target application may limit the rate actually achieved.
- Adjust **Shape size** to set the circle diameter or the square/triangle side length, then choose **Circle**, **Triangle**, or **Square** to follow it near the current pointer position.
- Draw a stroke and select **Use Drawn Path** to scale it across the full display. **Random** generates a screen-wide random route. Adjust movement speed with its slider.
- Press **Ctrl+Alt+A** to toggle the clicker, **Ctrl+Alt+P** to toggle path following, or **Ctrl+Alt+S** to stop all activity.
- Press **Ctrl+Alt+Num1** for Circle, **Ctrl+Alt+Num2** for Triangle, **Ctrl+Alt+Num3** for Square, or **Ctrl+Alt+Num4** for Random. Enable Num Lock when using the numeric keypad.
- Moving the mouse manually disengages the active action. Reactivate it from the UI or a hotkey.

The two movement modes cannot run at the same time. Use the **Stop All** button or the stop hotkey whenever you need to halt activity immediately.
