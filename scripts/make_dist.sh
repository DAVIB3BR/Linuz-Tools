#!/usr/bin/env bash
# lunuz tools - gera todos os pacotes em dist/
#   .deb .rpm .pkg.tar.zst  +  .tar .tar.gz .tar.bz2 .tar.xz .tar.zst .zip
#   + flatpak (manifest/ref) + snap (yaml) + repo dnf/yum
# Uso: bash scripts/make_dist.sh
set -eu
cd "$(dirname "$0")/.."
ROOT="$PWD"
VER=$(python3 -c "import sys; sys.path.insert(0,'.'); from lunuz import __version__; print(__version__)")
NAME="lunuz-tools"
DIST="$ROOT/dist"
STAGE="$DIST/stage"
rm -rf "$DIST"
mkdir -p "$DIST" "$STAGE"

echo "== lunuz tools $VER - gerando pacotes =="

# ------------------------------------------------------------------
# 1) rootfs (layout de instalacao: deb / rpm / pkg arch)
# ------------------------------------------------------------------
ROOTFS="$STAGE/rootfs"
mkdir -p "$ROOTFS/usr/bin" \
         "$ROOTFS/usr/share/applications" \
         "$ROOTFS/usr/share/icons/hicolor/128x128/apps"
rsync -a --delete --exclude '__pycache__' "$ROOT/lunuz" "$ROOTFS/usr/lib/"
cat > "$ROOTFS/usr/bin/lunuz" <<'WRAP'
#!/bin/sh
# lunuz tools - wrapper instalado pelo pacote
export PYTHONPATH="/usr/lib/lunuz${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m lunuz "$@"
WRAP
chmod 755 "$ROOTFS/usr/bin/lunuz"
sed -e 's|^Exec=lunuz$|Exec=lunuz gui|' -e 's|^Exec=lunuz --help$|Exec=lunuz --help|' \
    "$ROOT/AppDir/lunuz.desktop" > "$ROOTFS/usr/share/applications/lunuz-tools.desktop"
cp "$ROOT/AppDir/lunuz.png" "$ROOTFS/usr/share/icons/hicolor/128x128/apps/lunuz.png"

# ------------------------------------------------------------------
# 2) arvore de fonte (tars / zip)
# ------------------------------------------------------------------
SRC="$STAGE/lunuz-tools-$VER"
mkdir -p "$SRC/scripts"
rsync -a --delete --exclude '__pycache__' "$ROOT/lunuz" "$SRC/"
rsync -a --delete "$ROOT/tests" "$SRC/"
cp "$ROOT/README.md" "$ROOT/README.pt-BR.md" "$ROOT/setup.py" \
   "$ROOT/AppRun.sh" "$ROOT/org.davi.lunuz-tools.json" \
   "$ROOT/snapcraft.yaml" "$ROOT/lunuz.flatpakref" \
   "$ROOT/scripts/make_dist.sh" "$SRC/" 2>/dev/null || true
mv -f "$SRC/make_dist.sh" "$SRC/scripts/make_dist.sh" 2>/dev/null || true

# ------------------------------------------------------------------
# 3) tarballs + zip (codigo)
# ------------------------------------------------------------------
echo "  - tar / tar.gz / tar.bz2 / tar.xz / tar.zst / zip"
( cd "$STAGE" && tar -cf         "$DIST/lunuz-tools-$VER.tar"          "lunuz-tools-$VER" )
( cd "$STAGE" && tar -czf        "$DIST/lunuz-tools-$VER.tar.gz"       "lunuz-tools-$VER" )
( cd "$STAGE" && tar -cjf        "$DIST/lunuz-tools-$VER.tar.bz2"      "lunuz-tools-$VER" )
( cd "$STAGE" && tar -cJf        "$DIST/lunuz-tools-$VER.tar.xz"       "lunuz-tools-$VER" )
( cd "$STAGE" && tar --zstd -cf  "$DIST/lunuz-tools-$VER.tar.zst"      "lunuz-tools-$VER" )
if command -v zip >/dev/null 2>&1; then
  ( cd "$STAGE" && zip -qr       "$DIST/lunuz-tools-$VER.zip"          "lunuz-tools-$VER" )
else
  # fallback sem o binario zip: usa o modulo zipfile do Python
  python3 - "$STAGE/lunuz-tools-$VER" "$DIST/lunuz-tools-$VER.zip" <<'PYZIP'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _dirs, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            zf.write(p, os.path.relpath(p, os.path.dirname(src)))
PYZIP
fi

# ------------------------------------------------------------------
# 4) .deb (Debian/Ubuntu)
# ------------------------------------------------------------------
if command -v dpkg-deb >/dev/null 2>&1; then
  echo "  - deb"
  mkdir -p "$ROOTFS/DEBIAN"
  ISIZE=$(du -sk "$ROOTFS/usr" | cut -f1)
  cat > "$ROOTFS/DEBIAN/control" <<CTRL
Package: lunuz-tools
Version: $VER
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-vte-2.91
Maintainer: Davi <davi@localhost>
Installed-Size: $ISIZE
Description: lunuz tools - CLI utilities with a LinuxToys-style GUI
 A collection of command line utilities (ls, grep, find, chmod, java,
 cpp, python, node...) plus a GTK interface with drivers, repositories,
 kernels, optimization, IDEs and programming language installers.
CTRL
  dpkg-deb --build --root-owner-group "$ROOTFS" "$DIST/${NAME}_${VER}_all.deb" >/dev/null
  rm -rf "$ROOTFS/DEBIAN"
elif command -v ar >/dev/null 2>&1; then
  # fallback sem dpkg-deb: monta o .deb na mao (ar + tars)
  echo "  - deb (fallback ar)"
  mkdir -p "$ROOTFS/DEBIAN"
  ISIZE=$(du -sk "$ROOTFS/usr" | cut -f1)
  cat > "$ROOTFS/DEBIAN/control" <<CTRL
Package: lunuz-tools
Version: $VER
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-vte-2.91
Maintainer: Davi <davi@localhost>
Installed-Size: $ISIZE
Description: lunuz tools - CLI utilities with a LinuxToys-style GUI
 A collection of command line utilities (ls, grep, find, chmod, java,
 cpp, python, node...) plus a GTK interface with drivers, repositories,
 kernels, optimization, IDEs and programming language installers.
CTRL
  DSTAGE="$STAGE/debstage"
  mkdir -p "$DSTAGE"
  echo "2.0" > "$DSTAGE/debian-binary"
  ( cd "$ROOTFS/DEBIAN" && tar --owner=0 --group=0 -czf "$DSTAGE/control.tar.gz" . )
  ( cd "$ROOTFS" && tar --owner=0 --group=0 -czf "$DSTAGE/data.tar.gz" ./usr )
  ( cd "$DSTAGE" && ar -r "$DIST/${NAME}_${VER}_all.deb" debian-binary control.tar.gz data.tar.gz >/dev/null )
  rm -rf "$DSTAGE" "$ROOTFS/DEBIAN"
else
  echo "  ! dpkg-deb e ar ausentes - .deb pulado"
fi

# ------------------------------------------------------------------
# 5) .rpm (Fedora/RHEL)
# ------------------------------------------------------------------
if command -v rpmbuild >/dev/null 2>&1; then
  echo "  - rpm"
  TOP="$DIST/rpmbuild"
  mkdir -p "$TOP/BUILD" "$TOP/RPMS" "$TOP/SOURCES" "$TOP/SPECS" "$TOP/SRPMS"
  cat > "$TOP/SPECS/lunuz-tools.spec" <<SPEC
Name: lunuz-tools
Version: $VER
Release: 1
Summary: CLI utilities with a LinuxToys-style GUI
License: Unspecified
URL: https://github.com/DAVIB3BR/Linuz-Tools
AutoReqProv: no
BuildArch: noarch
Requires: python3, python3-gobject, gtk3, vte291

%description
A collection of command line utilities (ls, grep, find, chmod, java,
cpp, python, node...) plus a GTK interface with drivers, repositories,
kernels, optimization, IDEs and programming language installers.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -a %{_sourcedir}/rootfs/. %{buildroot}/

%files
%defattr(-,root,root,-)
/usr/lib/lunuz
/usr/bin/lunuz
/usr/share/applications/lunuz-tools.desktop
/usr/share/icons/hicolor/128x128/apps/lunuz.png
SPEC
  rpmbuild -bb --define "_topdir $TOP" --define "_sourcedir $STAGE" \
      "$TOP/SPECS/lunuz-tools.spec" >/dev/null
  mv "$TOP"/RPMS/noarch/*.rpm "$DIST/${NAME}-${VER}-1.noarch.rpm"
else
  echo "  ! rpmbuild ausente - .rpm pulado"
fi

# ------------------------------------------------------------------
# 6) .pkg.tar.zst (Arch/Manjaro) - layout pacman manual
# ------------------------------------------------------------------
echo "  - pkg.tar.zst (arch)"
PKGDIR="$STAGE/pkg"
rm -rf "$PKGDIR"
mkdir -p "$PKGDIR"
cp -a "$ROOTFS/usr" "$PKGDIR/"
SIZE=$(du -sk "$PKGDIR/usr" | cut -f1)
cat > "$PKGDIR/.PKGINFO" <<PI
pkgname = $NAME
pkgver = $VER-1
pkgdesc = CLI utilities with a LinuxToys-style GUI
url = https://github.com/DAVIB3BR/Linuz-Tools
builddate = $(date +%s)
packager = Davi
size = $SIZE
arch = any
depends = python
depends = python-gobject
depends = gtk3
depends = vte3
PI
tar --zstd --owner=0 --group=0 -cf "$DIST/${NAME}-${VER}-1-any.pkg.tar.zst" \
    -C "$PKGDIR" .PKGINFO usr

# ------------------------------------------------------------------
# 7) flatpak / snap / repo dnf-yum
# ------------------------------------------------------------------
echo "  - flatpak / snap / repo"
cp "$ROOT/org.davi.lunuz-tools.json" "$DIST/"
cp "$ROOT/lunuz.flatpakref" "$DIST/"
cp "$ROOT/snapcraft.yaml" "$DIST/"
cat > "$DIST/lunuz-tools.repo" <<REPO
[lunuz-tools]
name=lunuz tools - \$basearch
baseurl=https://github.com/DAVIB3BR/Linuz-Tools/releases/latest/rpm
enabled=0
gpgcheck=0
REPO
cat > "$DIST/INSTALL.txt" <<TXT
lunuz tools $VER - como instalar cada formato
==============================================

.deb   sudo apt install ./${NAME}_${VER}_all.deb
.rpm   sudo dnf install ./${NAME}-${VER}-1.noarch.rpm
.pkg   sudo pacman -U ${NAME}-${VER}-1-any.pkg.tar.zst
tar    tar -xJf lunuz-tools-$VER.tar.xz && cd lunuz-tools-$VER && python3 -m lunuz gui
zip    unzip lunuz-tools-$VER.zip && cd lunuz-tools-$VER && python3 -m lunuz gui

flatpak (fonte):  flatpak-builder --user --install build org.davi.lunuz-tools.json
snap (fonte):     cd snapcraft.yaml-dir && snapcraft     (requer snapd)
dnf/yum repo:     hospede o .rpm em uma URL e adicione lunuz-tools.repo
                  sudo dnf config-manager --add-repo lunuz-tools.repo

ARM (aarch64): veja dist/arm/LEIA-ME.md - os mesmos pacotes all/noarch/any
               funcionam nativamente em ARM (Raspberry Pi, Fedora ARM...)
TXT

# ------------------------------------------------------------------
# 7.1) ARM (aarch64) - pacotes independentes de arquitetura
# ------------------------------------------------------------------
echo "  - arm (aarch64)"
mkdir -p "$DIST/arm"
for f in "${NAME}_${VER}_all.deb" "${NAME}-${VER}-1.noarch.rpm" \
         "${NAME}-${VER}-1-any.pkg.tar.zst" "lunuz-tools-$VER.tar.gz" \
         "lunuz-tools-$VER.tar.xz" "lunuz-tools-$VER.zip"; do
  [ -f "$DIST/$f" ] && cp "$DIST/$f" "$DIST/arm/"
done
cat > "$DIST/arm/LEIA-ME.md" <<ARM
# 🦾 lunuz tools $VER para ARM (aarch64)

> **Lunuz-Tools é 100% Python** — os pacotes são \`all\` / \`noarch\` / \`any\`
> (independentes de arquitetura). Isso significa que estes arquivos rodam
> **nativamente em ARM64** sem nenhuma alteração: os nomes não dizem
> "arm64" porque o pacote serve para **todas** as arquiteturas, inclusive
> ARM.

## 💻 Funciona em

- 🍓 Raspberry Pi OS (64-bit) / Raspberry Pi 4 e 5
- 🧊 Ubuntu/Debian ARM64 (M1/M2 com VM, Ampere, ...)
- 🎩 Fedora ARM64 / RHEL ARM
- 🎀 Manjaro/Arch ARM, openSUSE ARM

## 📥 Instalação no ARM

| Formato | Comando |
|---------|---------|
| 🧊 Debian/Ubuntu/RPi OS | \`sudo apt install ./${NAME}_${VER}_all.deb\` |
| 🎩 Fedora ARM | \`sudo dnf install ./${NAME}-${VER}-1.noarch.rpm\` |
| 🎀 Arch/Manjaro ARM | \`sudo pacman -U ${NAME}-${VER}-1-any.pkg.tar.zst\` |
| 📦 Qualquer distro | \`tar -xJf lunuz-tools-$VER.tar.xz && cd lunuz-tools-$VER && python3 -m lunuz gui\` |

## ⚙️ Dependências da GUI no ARM

\`\`\`bash
# Debian/Ubuntu/RPi OS
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
# Fedora
sudo dnf install python3 python3-gobject gtk3 vte291
# Arch
sudo pacman -S python python-gobject gtk3 vte3
\`\`\`

## 🖼️ AppImage para ARM

- \`linuz_tools-aarch64.AppImage\` — AppImage nativo **ARM64** (runtime
  oficial do AppImageKit para aarch64)
- Assim como na versão x86_64, o AppImage usa o **Python 3 + GTK/VTE do
  sistema** (instale as dependências abaixo se necessário)

## ❓ E o AppImage x86_64?

O \`linuz_tools-x86_64.AppImage\` (na raiz do repositório) é o único
artefato restrito a x86_64. Para ARM use o \`linuz_tools-aarch64.AppImage\`
desta pasta ou os pacotes acima — o resultado é o mesmo app completo, com
as **14 seções / 112 recursos**, o suporte a **11 idiomas** e os
**repositórios automáticos**.

---
lunuz tools $VER 🌙 • https://github.com/DAVIB3BR/Linuz-Tools
ARM

# se o AppImage ARM estiver na raiz, inclua na pasta arm
[ -f "$ROOT/linuz_tools-aarch64.AppImage" ] && cp "$ROOT/linuz_tools-aarch64.AppImage" "$DIST/arm/" || true

# ------------------------------------------------------------------
# 8) verificacao
# ------------------------------------------------------------------
# remove intermediarios de build (staging + arvore do rpmbuild)
rm -rf "$STAGE" "$DIST/rpmbuild"

echo "== verificacao =="
if [ -f "$DIST/${NAME}_${VER}_all.deb" ]; then
  if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --info "$DIST/${NAME}_${VER}_all.deb" | sed -n '3,7p'
    echo "   arquivos: $(dpkg-deb --contents "$DIST/${NAME}_${VER}_all.deb" | wc -l)"
  else
    echo "   deb: $(ar t "$DIST/${NAME}_${VER}_all.deb" | tr '\n' ' ')"
  fi
fi
[ -f "$DIST/${NAME}-${VER}-1.noarch.rpm" ] && { rpm -qp --info "$DIST/${NAME}-${VER}-1.noarch.rpm" | sed -n '1,6p'; echo "   arquivos: $(rpm -qlp "$DIST/${NAME}-${VER}-1.noarch.rpm" | wc -l)"; } || true
echo "   pkg arch: $(tar --zstd -tf "$DIST/${NAME}-${VER}-1-any.pkg.tar.zst" | wc -l) arquivos"
echo "   zip:      $(python3 -c "import zipfile,sys; print(len(zipfile.ZipFile(sys.argv[1]).namelist()), 'arquivos')" "$DIST/lunuz-tools-$VER.zip" 2>/dev/null || echo '(ok)')"

echo
echo "OK - pacotes em $DIST:"
ls -la "$DIST" | grep -v '^d' | grep -v total
