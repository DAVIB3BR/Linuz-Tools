# 🦾 lunuz tools 1.0.5 para ARM (aarch64)

> **Lunuz-Tools é 100% Python** — os pacotes são `all` / `noarch` / `any`
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
| 🧊 Debian/Ubuntu/RPi OS | `sudo apt install ./lunuz-tools_1.0.5_all.deb` |
| 🎩 Fedora ARM | `sudo dnf install ./lunuz-tools-1.0.5-1.noarch.rpm` |
| 🎀 Arch/Manjaro ARM | `sudo pacman -U lunuz-tools-1.0.5-1-any.pkg.tar.zst` |
| 📦 Qualquer distro | `tar -xJf lunuz-tools-1.0.5.tar.xz && cd lunuz-tools-1.0.5 && python3 -m lunuz gui` |

## ⚙️ Dependências da GUI no ARM

```bash
# Debian/Ubuntu/RPi OS
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
# Fedora
sudo dnf install python3 python3-gobject gtk3 vte291
# Arch
sudo pacman -S python python-gobject gtk3 vte3
```

## 🖼️ AppImage para ARM

- `linuz_tools-aarch64.AppImage` — AppImage nativo **ARM64** (runtime
  oficial do AppImageKit para aarch64)
- Assim como na versão x86_64, o AppImage usa o **Python 3 + GTK/VTE do
  sistema** (instale as dependências abaixo se necessário)

## ❓ E o AppImage x86_64?

O `linuz_tools-x86_64.AppImage` (na raiz do repositório) é o único
artefato restrito a x86_64. Para ARM use o `linuz_tools-aarch64.AppImage`
desta pasta ou os pacotes acima — o resultado é o mesmo app completo, com
as **14 seções / 112 recursos**, o suporte a **11 idiomas** e os
**repositórios automáticos**.

---
lunuz tools 1.0.5 🌙 • https://github.com/DAVIB3BR/Linuz-Tools
