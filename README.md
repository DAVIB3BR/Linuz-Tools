# 🌙 lunuz tools (Linuz-Tools)

<div align="center">

**Version 1.0.5** 🏷️

Linux utility collection with a graphical interface inspired by
**LinuxToys** (section grid with icons, search and embedded terminal).

🖥️ **Debian/Ubuntu** • 🎀 **Arch/Manjaro** • 🎩 **Fedora/RHEL** • 🦎 **openSUSE** • 🎮 **SteamOS**

> 🇧🇷 Versão em português: [README.pt-BR.md](README.pt-BR.md)

</div>

---

## ✨ What it does

- 🪟 **Windows on Linux** — Wine, Steam, Lutris, Bottles, Proton-GE, WinBoat and more
- 🧰 **Drivers and Kernels** — NVIDIA, AMD, Intel, Realtek, XanMod, Liquorix, RT...
- 📦 **Automatic repositories** — the app adds any missing repository by itself
- 🌍 **11 languages** — detects your system language and switches instantly, no restart
- 🖲️ **Embedded terminal** — follow every install in real time

## 🗺️ Sections (**14 sections / 112 resources**)

| Section | Content |
|---------|---------|
| 🖥️ System | Detect hardware, info, failed services, boot |
| 🔄 Update System | Full update, Flatpak, Snap, package cache |
| 🧰 Drivers and Hardware | **NVIDIA** (install/fix/nouveau), **AMD**, Intel, **Realtek** (firmware + Wi-Fi DKMS), **Acer** (ACPI/fan), general firmware |
| 📡 Additional Repositories | **curl, git, flatpak, snapd, Homebrew, Nix, pip** + non-free (Debian), RPM Fusion (Fedora), multilib (Arch), Packman (openSUSE) |
| 🧠 Linux Kernels | Default, LTS, **Zen, XanMod, Liquorix, RT** (modified), **mainline download (kernel.org)**, list, remove old |
| 🚀 System Optimization | Quick optimize, ZRAM, swappiness, TRIM, cleanup, MAKEFLAGS, boot |
| 👨‍💻 Developers | Toolchains (OpenJDK, g++, Python, Node) and file runners |
| ✏️ IDEs, Editors and AI | **VS Code, VSCodium, Sublime Text, IntelliJ IDEA, PyCharm, Eclipse, Zed**; **Neovim, Vim, Emacs, Kate, GNOME, Nano**; AI agents **Ollama, Aider, Claude Code, Gemini CLI**; essential tools and **Docker** |
| 🪟 **Windows on Linux** | **Wine** (WineHQ repo auto-added), **Winetricks**, **Bottles**, **Lutris**, **ProtonUp-Qt** (Proton-GE), **Heroic**, **Steam**, **PlayOnLinux**, **WinBoat** (Windows 11 in a container) and **GameMode + MangoHud** |
| 🔤 Programming Languages | **Python 3 + pip, OpenJDK, Node.js LTS, C/C++, Rust, Go, Ruby, PHP** |
| 🩺 Health and Wellness | Report, disk, RAM, temperature, **SMART**, failures, updates |
| 🌐 Network and Internet | Status, Wi-Fi, firewall, **fix DNS** |
| 🧩 Utilities | All 21 CLI commands (ls, grep, find, chmod...) with dialogs |
| 💻 **Terminal** | Dedicated tab showing install progress (spinner, status, step counter) |

## 🪟 The «Windows on Linux» section

Everything you need to run Windows programs and games, **with the official
repositories enabled automatically** (WineHQ, multilib, RPM Fusion, Packman...):

| Item | What it does |
|------|--------------|
| 🍷 Wine | Run Windows `.exe` programs (WineHQ repo added by itself) |
| 🧪 Winetricks | Windows DLLs and components for Wine |
| 🍾 Bottles | Windows apps/games in isolated "bottles" (Flatpak) |
| 🎯 Lutris | Game hub with community installers |
| ⏫ ProtonUp-Qt | Install/update Steam's **Proton-GE** |
| 🦸 Heroic | Epic, GOG and Amazon Games on Linux |
| 🎮 Steam | Valve's store (enables multilib/RPM Fusion/Packman by itself) |
| 🐧 PlayOnLinux | Classic Wine assistant |
| 🚢 **WinBoat** | **Real Windows 11** in a Docker container, integrated with your desktop |
| ⚡ GameMode + MangoHud | Performance boost and FPS overlay |

## 📦 Automatic repositories (the v1.0.5 highlight)

💡 **Never see "package not found" because of a missing repository again.**
When you request a driver/kernel/app that needs a repository your distro
doesn't have, lunuz **adds the repository by itself** before installing:

| Action | Repository added automatically |
|--------|-------------------------------|
| 🧰 NVIDIA driver (Debian) | `contrib` + `non-free` + `non-free-firmware` |
| 🧰 NVIDIA driver (Fedora) | **RPM Fusion** (free + nonfree) |
| 🧰 NVIDIA driver (openSUSE) | Official NVIDIA repo |
| 🧰 AMD/Intel (Arch) | **multilib** (`lib32-*` packages) |
| 🧠 XanMod kernel (Debian) | **XanMod** repo + key |
| 🧠 XanMod kernel (Arch) | **chaotic-aur** (keyring + mirrorlist) |
| 🧠 Liquorix kernel (Debian) | **Liquorix** repo + key |
| 🎮 Steam (Fedora/Arch/openSUSE) | RPM Fusion / multilib / Packman |
| 🍷 Wine (Debian) | **WineHQ** (falls back to the distro package) |
| 🚢 WinBoat | Docker + latest GitHub release download |

## 🌍 11 languages, automatic detection

The interface detects your system language (`LANG`/`LC_ALL`) and applies the
matching translation — **English (US) is the default** when the language is
not supported. To switch manually:

> ⚙️ **Gear icon in the header → Settings → Language**

| 🏳️ Languages |
|---------------|
| 🇺🇸 English (US) 🇬🇧 English (UK) 🇦🇺 English (Australia) 🇧🇷 Português (Brasil) 🇵🇹 Português (Portugal) 🇷🇺 Русский 🇯🇵 日本語 🇨🇳 中文（简体） 🇩🇪 Deutsch 🇰🇷 한국어 🇻🇳 Tiếng Việt |

- Switching is **instant** (no app restart) and saved to
  `~/.config/lunuz/settings.json`
- It translates **everything**: sections, items, search, dialogs, run
  queue and the `lunuz distro` command

## 🖥️ Interface (LinuxToys style)

- ✨ **A distinct icon for each of the 112 resources**, with brand icons
  (NVIDIA, AMD, Docker, VS Code, Python...) and colorful generated squares
  for the rest
- 🆔 **Distro chip** on the home screen: logo, family and how many actions
  are available; actions from other distros are dimmed with an
  "only on..." badge
- 🔍 **Instant search** filtering all 112 resources (in your language)
- 🔲 **Grid/list** toggles in the header
- ✅ **Multi-select**: pick several items and run them **in sequence with a
  single confirmation**
- 🚦 **Execution queue**: one action at a time — output never mixes
- ⌨️ `Esc` clears search/returns home • `Ctrl+F` focuses search • **back**
  button always available
- 🔐 Admin actions use **pkexec**; dangerous ones ask for **prior
  confirmation**

## 🚀 Running it as an APP (no terminal needed)

1. 🖱️ **Double-click** `linuz_tools-x86_64.AppImage` — the GUI opens by itself
2. 📋 Search **"lunuz tools"** in the applications menu
3. 🖼️ `lunuz-tools.desktop` icon on the desktop

### Advanced options (terminal)

```bash
lunuz gui                      # graphical interface
./linuz_tools-x86_64.AppImage --help                        # direct CLI
./linuz_tools-x86_64.AppImage --appimage-extract-and-run    # WITHOUT FUSE
```

> 💡 If the AppImage cannot mount (FUSE missing), use
> `--appimage-extract-and-run`. Without GTK/VTE, a popup (zenity) explains
> what to install.

## ⌨️ CLI commands (22)

| Category | Commands |
|----------|----------|
| 📁 Files | `ls` `pwd` `cd` `cat` `echo` `mkdir` `rm` `cp` `mv` |
| 🔎 Search | `grep` `find` |
| 🔐 Permissions | `chmod` (numeric **and symbolic**: `+x`, `u+x`, `go-w`) `chown` |
| 🗣️ Languages | `java` `cpp` `python` `node` `shell` |
| 🛠️ System | `openjdk` `distro` `gui` `--version` |

```bash
lunuz ls -la /tmp
lunuz cpp main.cpp              # compiles and runs C++
lunuz chmod +x script.sh        # symbolic mode now works!
lunuz distro                    # distro + actions available here
lunuz distro --list             # lists every available action
lunuz gui                       # graphical interface
```

## 📥 Installing

Pre-built artifacts live in `dist/` (build them yourself with
`scripts/make_dist.sh`):

| Format | File | Install |
|--------|------|---------|
| 🧊 Debian/Ubuntu | `lunuz-tools_1.0.5_all.deb` | `sudo apt install ./lunuz-tools_1.0.5_all.deb` |
| 🎩 Fedora/RHEL | `lunuz-tools-1.0.5-1.noarch.rpm` | `sudo dnf install ./lunuz-tools-1.0.5-1.noarch.rpm` |
| 🎀 Arch/Manjaro | `lunuz-tools-1.0.5-1-any.pkg.tar.zst` | `sudo pacman -U ...pkg.tar.zst` |
| 📦 Tarballs/Zip | `.tar.gz` `.tar.xz` `.zip`... | extract anywhere, run `python3 -m lunuz gui` |
| 🐞 Flatpak | `org.davi.lunuz-tools.json` | `flatpak-builder build org.davi.lunuz-tools.json` |
| 🦑 Snap | `snapcraft.yaml` | `snapcraft` |

### GUI dependencies

| Distro | Packages |
|--------|----------|
| 🧊 Debian/Ubuntu | `sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91` |
| 🎩 Fedora/RHEL | `sudo dnf install python3 python3-gobject gtk3 vte291` |
| 🎀 Arch/Manjaro | `sudo pacman -S python python-gobject gtk3 vte3` |
| 🦎 openSUSE | `sudo zypper in python3 python3-gobject gtk3 vte-2_91` |
| 🎮 SteamOS | AppImage with `--appimage-extract-and-run` |

## ✅ Tests

Three automated suites cover the whole interface (navigation, search, back
button, view toggles, all 112 items, the execution queue with real terminal
output, multi-select and every dialog):

```bash
python3 tests/test_gui_programatic.py   # 🎛️ tiles/search/back + 112 items
python3 tests/test_terminal_queue.py    # 🚦 real queue: serialization + progress
python3 tests/test_gui_dialogs.py       # 💬 real form/file-chooser/confirmation
```

## 🗂️ Structure

```
lunuz_tools/
├── lunuz/                  # Python package
│   ├── cli.py              # CLI (22 commands)
│   ├── gui.py              # GTK3 + VTE interface
│   ├── actions.py          # action catalog (per-distro scripts)
│   ├── tools.py            # command line utilities
│   ├── i18n.py             # 🌍 language detection + switching
│   ├── ui_translations.py  # interface texts (11 languages)
│   ├── item_translations.py# item names/descriptions (8 languages)
│   └── icons/              # per-section/item/distro icons
├── tests/                  # 3 GUI test suites
├── scripts/                # make_dist.sh + icon generator
├── dist/                   # generated packages
└── linuz_tools-x86_64.AppImage
```

## 🤝 Contributing

1. 🍴 Fork it
2. 🌱 Create your branch (`git checkout -b my-feature`)
3. ✅ Run the tests
4. 📤 Open a Pull Request

---

<div align="center">

Made with 💙 for Linux • [Report a Bug](https://github.com/DAVIB3BR/Linuz-Tools/issues) • [Repository](https://github.com/DAVIB3BR/Linuz-Tools)

</div>
