# Whisper Tray

A system tray applet with a bundled whisper.cpp to transcribe audio.

## Features

*   Record audio from microphone and transcribe it using whisper.cpp.
*   System tray icon with status indicators (idle, recording, processing).
*   Configurable hotkey to start/stop recording.
*   Settings window to configure:
    *   Whisper.cpp executable path.
    *   Model directory and specific model file.
    *   Language for transcription.
    *   Hotkey combination.
    *   Output mode (clipboard, type automatically, or both).
    *   Autostart at login.
    *   Enable/disable notifications and recording start sound.
*   Transcription history viewer.
*   Option to download whisper.cpp models directly from the application.

## Installation

### Arch Linux (AUR)

The application is available on the Arch User Repository (AUR) as `whisper-tray`. You can install it using an AUR helper like `yay` or `paru`:

```bash
yay -S whisper-tray
```

or

```bash
paru -S whisper-tray
```

### Manual Installation

1.  Ensure all dependencies are installed (see Dependencies section).
2.  Clone this repository or download the source code.
3.  Follow the instructions in the "Building from source" section.
4.  Run `whisper-tray.py`.

## Usage

After installation, launch "Whisper Tray" from your application menu or by running `whisper-tray` in the terminal.

*   **Tray Icon**:
    *   Left-click or activate the "Record" / "Stop Recording" menu item to toggle audio recording.
    *   The icon changes to indicate the current state:
        *   Idle: Ready to record.
        *   Recording: Currently recording audio.
        *   Processing: Transcribing audio.
*   **Hotkey**: Press the configured hotkey (default: `Ctrl+Alt+H`) to start or stop recording.
*   **Settings**: Right-click the tray icon and select "Settings" to configure the application.
*   **History**: Right-click the tray icon and select "History" to view recent transcriptions.
*   **Quit**: Right-click the tray icon and select "Quit" to close the application.

## Configuration

Configuration settings are stored in `~/.config/whisper-tray/config.json`. You can modify these settings through the Settings window. Key settings include:

*   `executable`: Path to the `whisper-tray-cli` (or your custom whisper.cpp) executable.
*   `model_path`: Full path to the whisper.cpp model file (e.g., `~/.local/share/whisper_models/ggml-base.en.bin`).
*   `model_dir`: Directory where models are stored and searched for.
*   `hotkey`: Hotkey string (e.g., `ctrl+alt+h`).
*   `language`: Language code for transcription (e.g., `en`, `es`, `auto`).
*   `output_mode`: How the transcribed text is output (`clipboard`, `type`, `both`).
*   `enable_notifications`: `true` or `false`.
*   `enable_sound`: `true` or `false`.

Whisper.cpp models can be downloaded via the "Download..." button in the Settings window if they are not already present in your model directory.

## Dependencies

*   `python-gobject`
*   `python-sounddevice`
*   `python-numpy`
*   `python-scipy`
*   `python-pynput`
*   `libappindicator-gtk3`
*   `libnotify`
*   `xclip`
*   `ffmpeg` (for playing start sound and potentially for `whisper.cpp` if not using a pre-built `whisper-tray-cli`)
*   `ggml-vulkan-git` (or other GGML provider for `whisper.cpp`)
*   `sdl2-compat` (for `whisper.cpp`)
*   `vulkan-icd-loader` (for `whisper.cpp` with Vulkan support)

## Building from source

To build the bundled `whisper.cpp` (which becomes `whisper-tray-cli`):

1.  Ensure the `makedepends` are installed:
    *   `cmake`
    *   `git`
    *   `vulkan-headers`
2.  Clone the repository and navigate into the `whisper.cpp-1.7.6` directory (or the version specified in `PKGBUILD`).
3.  Run the following commands:

    ```bash
    cd whisper.cpp-1.7.6 # Adjust version if necessary
    cmake -B build -S . \
      -DCMAKE_INSTALL_PREFIX=/usr \
      -DCMAKE_BUILD_TYPE=Release \
      -DWHISPER_SDL2=ON \
      -DWHISPER_USE_SYSTEM_GGML=1
    cmake --build build
    ```
4.  The `whisper-tray-cli` executable will be at `build/bin/main`. The `PKGBUILD` installs this to `/usr/bin/whisper-tray-cli`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
The bundled `whisper.cpp` also uses the MIT License.
