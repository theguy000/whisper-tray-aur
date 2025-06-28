# Maintainer: TheGuy000 <istiakm30@gmail.com>

pkgname='whisper-tray'
# Use the git commit hash to create a version number that automatically updates.
# This format is standard for AUR VCS (Version Control System) packages.
pkgver() {
  cd "$pkgname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}
pkgrel=1
pkgdesc="A system tray applet with a bundled whisper.cpp to transcribe audio."
arch=('x86_64' 'aarch64')
url="https://github.com/theguy000/whisper-tray-aur"
license=('MIT')

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
# This lets users know this package provides the functionality of the base name
provides=("${pkgname}")
conflicts=("${pkgname}")

# This is the key part: we are sourcing from YOUR git repo and whisper.cpp's repo.
source=(
    "$pkgname::git+$url.git"
    "whisper.cpp.tar.gz::https://github.com/ggerganov/whisper.cpp/archive/refs/tags/v1.6.0.tar.gz" # Using a fixed, known-good version of whisper.cpp
)

sha256sums=('SKIP' # For the git repo
            '69b92a2a0962970731a55b63212870599a374636f237435f3089d36154562c23') # Checksum for v1.6.0

build() {
  # Build whisper.cpp
  cd "whisper.cpp-1.6.0"
  cmake \
    -B build \
    -S . \
    -DCMAKE_BUILD_TYPE=Release \
    -DWHISPER_VULKAN=ON

  cmake --build build
}

package() {
    # Install the uniquely named whisper.cpp binary from the build
    install -Dm755 "${srcdir}/whisper.cpp-1.6.0/build/bin/whisper-cli" "${pkgdir}/usr/bin/${pkgname}-cli"

    # Go into the source directory of your application (cloned from git)
    cd "${srcdir}/${pkgname}"

    # Install the main Python script
    install -Dm755 "${pkgname}.py" "${pkgdir}/usr/bin/${pkgname}"

    # Install the icons to a private directory for your app
    _icondir="${pkgdir}/usr/share/${pkgname}/icons"
    install -d "${_icondir}"
    install -Dm644 "icon-idle.svg" "${_icondir}/icon-idle.svg"
    install -Dm644 "icon-recording.svg" "${_icondir}/icon-recording.svg"
    install -Dm644 "icon-processing.svg" "${_icondir}/icon-processing.svg"

    # Automatically modify the installed script to use the correct paths
    sed -i "s|ICON_DIR = SCRIPT_DIR|ICON_DIR = '${_icondir}'|" "${pkgdir}/usr/bin/${pkgname}"
    sed -i "s|\"executable\": \"whisper-cli\"|\"executable\": \"${pkgname}-cli\"|" "${pkgdir}/usr/bin/${pkgname}"

    # Create a .desktop file for the application launcher
    install -Dm644 - "${pkgdir}/usr/share/applications/${pkgname}.desktop" <<EOF
[Desktop Entry]
Name=Whisper Tray
Comment=Record audio and transcribe it to the clipboard
Exec=${pkgname}
Icon=${pkgname}
Categories=Utility;AudioVideo;
Terminal=false
Type=Application
EOF
    # Install a generic icon for the .desktop file itself
    install -Dm644 "icon-idle.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"

    # Install the whisper.cpp license
    install -Dm644 "${srcdir}/whisper.cpp-1.6.0/LICENSE" \
        -t "${pkgdir}/usr/share/licenses/${pkgname}"
}