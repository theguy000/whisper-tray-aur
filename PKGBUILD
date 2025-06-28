# Maintainer: TheGuy000 <istiakm30@gmail.com>

pkgname='whisper-tray-git'
# 1. ADD A STATIC PKGVER - This is used by --printsrcinfo
#    It can be anything. 0.1, 1.0, etc. It's just a placeholder.
pkgver=1.0
pkgrel=1
pkgdesc="A system tray applet with a bundled whisper.cpp to transcribe audio."
arch=('x86_64' 'aarch64')
url="https://github.com/theguy000/whisper-tray-aur"
license=('MIT')

# 2. THE PKGVER() FUNCTION - This will run during the actual build
#    and override the static pkgver above.
pkgver() {
  cd "whisper-tray-aur" # No need for $srcdir here, makepkg handles it.
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

# --- The rest of the file is identical ---

# Dependencies to RUN the app
depends=(
    'python-gobject'
    'python-sounddevice'
    'python-numpy'
    'python-scipy'
    'python-pyperclip'
    'python-notifypy'
    'python-pynput'
    'libappindicator-gtk3'
    'vulkan-icd-loader'
    'xclip'
)
# Dependencies to BUILD the app (and whisper.cpp)
makedepends=(
    'cmake'
    'git'
    'vulkan-headers'
)
# We do NOT use provides=() or conflicts=() because this is a
# self-contained package and does not provide 'whisper.cpp' to the system.

source=(
    "whisper-tray-aur::git+$url.git"
    "whisper.cpp-1.6.0.tar.gz::https://github.com/ggerganov/whisper.cpp/archive/refs/tags/v1.6.0.tar.gz"
)

sha256sums=('SKIP'
            '69b92a2a0962970731a55b63212870599a374636f237435f3089d36154562c23')

build() {
  cd "whisper.cpp-1.6.0"
  cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DWHISPER_VULKAN=ON
  cmake --build build
}

package() {
    install -Dm755 "${srcdir}/whisper.cpp-1.6.0/build/bin/whisper-cli" "${pkgdir}/usr/bin/whisper-tray-cli"
    cd "${srcdir}/whisper-tray-aur"
    install -Dm755 "whisper-tray.py" "${pkgdir}/usr/bin/whisper-tray"
    _icondir="${pkgdir}/usr/share/whisper-tray/icons"
    install -d "${_icondir}"
    install -Dm644 "icon-idle.svg" "${_icondir}/icon-idle.svg"
    install -Dm644 "icon-recording.svg" "${_icondir}/icon-recording.svg"
    install -Dm644 "icon-processing.svg" "${_icondir}/icon-processing.svg"
    sed -i "s|ICON_DIR = SCRIPT_DIR|ICON_DIR = '${_icondir}'|" "${pkgdir}/usr/bin/whisper-tray"
    sed -i "s|\"executable\": \"whisper-cli\"|\"executable\": \"whisper-tray-cli\"|" "${pkgdir}/usr/bin/whisper-tray"
    install -Dm644 - "${pkgdir}/usr/share/applications/whisper-tray.desktop" <<EOF
[Desktop Entry]
Name=Whisper Tray
Comment=Record audio and transcribe it to the clipboard
Exec=whisper-tray
Icon=whisper-tray
Categories=Utility;AudioVideo;
Terminal=false
Type=Application
EOF
    install -Dm644 "icon-idle.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/whisper-tray.svg"
    install -Dm644 "${srcdir}/whisper.cpp-1.6.0/LICENSE" -t "${pkgdir}/usr/share/licenses/whisper-tray"
}