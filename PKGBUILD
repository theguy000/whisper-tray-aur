# Maintainer: TheGuy000 <istiakm30@gmail.com>

pkgname='whisper-tray'
pkgver=1.0
pkgrel=1
pkgdesc="A system tray applet with a bundled whisper.cpp to transcribe audio."
arch=('x86_64' 'aarch64')
url="https://github.com/theguy000/whisper-tray-aur"
license=('MIT')

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
makedepends=('cmake' 'git' 'vulkan-headers')

source=(
    "$pkgname-$pkgver.tar.gz::https://github.com/theguy000/whisper-tray-aur/archive/refs/heads/main.tar.gz"
    "whisper.cpp-1.7.6.tar.gz::https://github.com/ggerganov/whisper.cpp/archive/refs/tags/v1.7.6.tar.gz"
)

sha256sums=('cca565a59afc607e06bc5f06c5dc64dd587401f885d29f204159ca57fadac65e'
            '166140e9a6d8a36f787a2bd77f8f44dd64874f12dd8359ff7c1f4f9acb86202e')

build() {
  # The main tar.gz will extract to whisper-tray-aur-main, cd into that first
  # The README.md is a local file, sourced into srcdir directly.
  # The PKGBUILD expects whisper.cpp to be in srcdir, so we might need to adjust paths if
  # the main tarball structure is different than expected.
  # For now, assuming the build commands work as originally intended relative to srcdir.
  cd "${srcdir}/whisper.cpp-1.7.6"

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

    _icondir="${pkgdir}/usr/share/${pkgname}/icons"
    install -d "${_icondir}"
    install -Dm644 "icon-idle.svg" "${_icondir}/icon-idle.svg"
    install -Dm644 "icon-recording.svg" "${_icondir}/icon-recording.svg"
    install -Dm644 "icon-processing.svg" "${_icondir}/icon-processing.svg"

    _sounddir="${pkgdir}/usr/share/${pkgname}/sounds"
    install -d "${_sounddir}"
    install -Dm644 "sounds/on.mp3" "${_sounddir}/on.mp3"

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
    install -Dm644 "icon-idle.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
    install -Dm644 "LICENSE" -t "${pkgdir}/usr/share/licenses/${pkgname}"
    install -Dm644 "${srcdir}/whisper.cpp-1.7.6/LICENSE" -t "${pkgdir}/usr/share/licenses/${pkgname}"
}
