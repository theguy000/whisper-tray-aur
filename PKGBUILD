# Maintainer: TheGuy000 <istiakm30@gmail.com>

# This is a stable release package
pkgname='whisper-tray'
pkgver=1.0
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
    'python-pynput'
    'libappindicator-gtk3'
    'libnotify'
    'xclip'
    'ffmpeg'
    'ggml-vulkan-git'
    'sdl2-compat'
    'vulkan-icd-loader'
)
# Dependencies to BUILD the app (and whisper.cpp)
makedepends=('cmake' 'git' 'vulkan-headers')

# Point to a downloadable .tar.gz archive of your repository.
source=(
    "$pkgname-$pkgver.tar.gz::https://github.com/theguy000/whisper-tray-aur/archive/refs/heads/main.tar.gz"
    "whisper.cpp-1.7.6.tar.gz::https://github.com/ggerganov/whisper.cpp/archive/refs/tags/v1.7.6.tar.gz"
)

# Remember to replace the first checksum with the real one you generate.
sha256sums=('SKIP'
            'SKIP')

build() {
  cd "whisper.cpp-1.7.6"

  cmake -B build -S . \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_BUILD_TYPE=Release \
    -DWHISPER_SDL2=ON \
    -DWHISPER_USE_SYSTEM_GGML=1

  cmake --build build
}

package() {
    DESTDIR="${pkgdir}" cmake --install "${srcdir}/whisper.cpp-1.7.6/build"
    install -Dm755 "${srcdir}/whisper.cpp-1.7.6/build/bin/main" "${pkgdir}/usr/bin/${pkgname}-cli"
    cd "${srcdir}/whisper-tray-aur-main"
    install -Dm755 "whisper-tray.py" "${pkgdir}/usr/bin/${pkgname}"

    # Install icons to a private directory
    _icondir="${pkgdir}/usr/share/${pkgname}/icons"
    install -d "${_icondir}"
    install -Dm644 "icon-idle.svg" "${_icondir}/icon-idle.svg"
    install -Dm644 "icon-recording.svg" "${_icondir}/icon-recording.svg"
    install -Dm644 "icon-processing.svg" "${_icondir}/icon-processing.svg"

    # Create the launcher file
    _desktop_file="${srcdir}/${pkgname}.desktop"
    cat > "${_desktop_file}" <<EOF
[Desktop Entry]
Name=Whisper Tray
Comment=Record audio and transcribe it to the clipboard
Exec=${pkgname}
Icon=${pkgname}
Categories=Utility;AudioVideo;
Terminal=false
Type=Application
EOF
    install -Dm644 "${_desktop_file}" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    # Install the icon for the launcher itself
    install -Dm644 "icon-idle.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
    # Install licenses
    install -Dm644 "LICENSE" -t "${pkgdir}/usr/share/licenses/${pkgname}"
    install -Dm644 "${srcdir}/whisper.cpp-1.7.6/LICENSE" -t "${pkgdir}/usr/share/licenses/${pkgname}"
}
