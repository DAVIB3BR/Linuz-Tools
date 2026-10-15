# lunuz tools

Linux CLI utility collection with a graphical interface inspired by
**LinuxToys** (section grid with icons, search and embedded terminal).
Works on Debian/Ubuntu, Arch/Manjaro, Fedora/RHEL, openSUSE, SteamOS
and derivatives.

> The original Portuguese version is available in [README.pt-BR.md](README.pt-BR.md).

## Graphical interface (LinuxToys style)

Double-click the AppImage, the desktop icon or "lunuz tools" in the
applications menu. Available sections (**13 sections / 102 resources**):

| Section | Content |
|---------|---------|
| System | Detect hardware, info, failed services, boot |
| Update System | Full update, Flatpak, Snap, package cache |
| Drivers and Hardware | **NVIDIA** (install/fix/nouveau), **AMD**, Intel, **Realtek** (firmware + Wi-Fi DKMS), **Acer** (ACPI/fan), general firmware |
| Additional Repositories | **curl, git, flatpak, snapd, Homebrew, Nix, pip** + non-free (Debian), RPM Fusion (Fedora), multilib (Arch), Packman (openSUSE) |
| Linux Kernels | Default, LTS, **Zen, XanMod, Liquorix, RT** (modified), **mainline download (kernel.org)**, list, remove old |
| System Optimization | Quick optimize, ZRAM, swappiness, TRIM, cleanup, MAKEFLAGS, boot |
| Developers | Install toolchains (OpenJDK, g++, Python, Node) and run files |
| IDEs, Editors and AI | **VS Code, VSCodium, Sublime Text, IntelliJ IDEA, PyCharm, Eclipse, Zed**; **Neovim, Vim, Emacs, Kate, GNOME Text Editor, Nano**; AI agents **Ollama, Aider, Claude Code, Gemini CLI**; essential tools and **Docker** |
| Programming Languages | **Python 3 + pip, OpenJDK (Java), Node.js LTS, C/C++, Rust, Go, Ruby, PHP** |
| Health and Wellness | Report, disk, RAM, temperature, **SMART**, failures, updates |
| Network and Internet | Status, Wi-Fi, firewall, **fix DNS** |
| Utilities | All 21 CLI commands (ls, grep, find, chmod...) with dialogs |
| **Terminal** | **Dedicated tab that shows install progress** (spinner, status, step counter) |

Interface features:

- **A distinct icon for each of the 102 resources** (LinuxToys style),
  with **brand icons where they matter** (NVIDIA, AMD, Intel, Docker,
  VS Code, Python, Java, Rust...) and colorful generated icons for the
  rest, plus icons in the section header and action buttons
- **Distro identifier**: a chip on the home screen shows the detected
  distro (logo, family, version) and how many of the 102 actions are
  available here; actions from other distros are dimmed with an
  "only in ..." badge and clicking them explains where they work —
  `lunuz distro` does the same from the terminal (add `--list`)
- **Search** in the header filters all 102 resources
- **Grid/list modes** in the header
- **Multi-selection**: toggle "Seleção múltipla", pick several shell
  items and run them **in sequence with one confirmation**
- **Execution queue**: actions run one at a time — output never gets
  mixed up; progress is shown in the **Terminal tab** and in the status line
- **Back button** returns category → home (and search → origin page);
  `Esc` clears the search / goes home, `Ctrl+F` focuses the search
- Embedded **VTE terminal** shows the output of every action
- Administrative actions use **pkexec** (asks for authentication) and
  dangerous ones (drivers/kernels) ask for **prior confirmation**
- Scripts are automatically adapted to your detected distro

## Running it as an APP (no terminal needed)

### 1. Double-click the AppImage
Just double-click `lunuz-x86_64.AppImage` — **the GUI opens
automatically** (like a normal program).

### 2. Applications menu (KDE/GNOME)
Search for **"lunuz tools"** in the applications menu — it is registered.

### 3. Desktop icon
`lunuz-tools.desktop` on the desktop (marked trusted, double-click
opens the app).

### Advanced options (terminal)
```bash
lunuz gui            # graphical interface
./lunuz-x86_64.AppImage --help          # direct CLI
./lunuz-x86_64.AppImage --appimage-extract-and-run --help   # WITHOUT FUSE
```

> If the AppImage cannot mount (FUSE missing), use
> `--appimage-extract-and-run` or the `~/bin/lunuz-appimage.sh` script —
> works on any distro. If the GUI misses dependencies, a popup (zenity)
> explains what to install.

## Commands (22 in total)

| Category | Commands |
|----------|----------|
| Files | `ls` `pwd` `cd` `cat` `echo` `mkdir` `rm` `cp` `mv` |
| Search | `grep` `find` |
| Permissions | `chmod` `chown` |
| Languages | `java` (OpenJDK) `cpp` (g++) `python` `node` `shell` |
| System | `openjdk` (toolchain) `distro` (identify distro + available actions) `gui` (interface) `--version` |

Examples:

```bash
lunuz ls -la /tmp
lunuz cpp main.cpp          # compiles and runs C++
lunuz java Main.java        # runs Java (source-launch JDK 11+)
lunuz openjdk               # shows OpenJDK toolchain (java/javac/JAVA_HOME)
lunuz distro                # distro identifier + actions available here
lunuz distro --list         # lists every action available on this distro
lunuz shell script.sh arg1
lunuz grep -r TODO /home    # recursive search (directories and binaries safe)
lunuz gui                   # graphical interface
```

## Installing the packages

Pre-built artifacts live in `dist/` (build them yourself with
`scripts/make_dist.sh`):

| Format | File | Install |
|--------|------|---------|
| Debian/Ubuntu | `lunuz-tools_1.2.0_all.deb` | `sudo apt install ./lunuz-tools_1.2.0_all.deb` |
| Fedora/RHEL | `lunuz-tools-1.2.0-1.noarch.rpm` | `sudo dnf install ./lunuz-tools-1.2.0-1.noarch.rpm` |
| Arch/Manjaro | `lunuz-tools-1.2.0-1-any.pkg.tar.zst` | `sudo pacman -U lunuz-tools-1.2.0-1-any.pkg.tar.zst` |
| Source/binary tarballs | `.tar.gz` `.tar.bz2` `.tar.xz` `.tar.zst` `.tar` | extract anywhere, run `python3 -m lunuz gui` |
| Zip | `lunuz-tools-1.2.0.zip` | same as tarballs |
| Flatpak | `org.davi.lunuz-tools.json` / `lunuz.flatpakref` | `flatpak-builder build org.davi.lunuz-tools.json` |
| Snap | `snapcraft.yaml` | `snapcraft` (needs snapd) |
| dnf/yum repo | `lunuz-tools.repo` | `sudo dnf config-manager --add-repo lunuz-tools.repo` (host the rpm first) |

GUI dependencies per distro:

| Distro | Packages |
|--------|----------|
| Debian/Ubuntu | `sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91` |
| Fedora/RHEL | `sudo dnf install python3 python3-gobject gtk3 vte291` |
| Arch/Manjaro | `sudo pacman -S python python-gobject gtk3 vte3` |
| openSUSE | `sudo zypper in python3 python3-gobject gtk3 vte-2_91` |
| SteamOS (read-only) | use the AppImage with `--appimage-extract-and-run` |

Compilers/languages (optional):

```bash
# Debian/Ubuntu: sudo apt install default-jdk g++ nodejs
# Fedora:        sudo dnf install java-21-openjdk-devel gcc-c++ nodejs
# Arch:          sudo pacman -S jdk-openjdk gcc nodejs
# openSUSE:      sudo zypper in java-21-openjdk-devel gcc-c++ nodejs
```

## Tests

Three automated suites cover the whole interface (navigation, search,
back button, view toggles, all 102 items, the execution queue with real
terminal output, multi-selection and every dialog):

```bash
python3 tests/test_gui_programatic.py   # tiles/search/back/toggles + 102 items
python3 tests/test_terminal_queue.py    # real queue: serialization + progress
python3 tests/test_gui_dialogs.py       # real form/file-chooser/confirmation
```

## Structure

```
lunuz_tools/
├── lunuz/              # Python package (cli.py, tools.py, gui.py, actions.py)
├── tests/              # GUI test suites
├── scripts/
│   └── make_dist.sh    # builds deb, rpm, pkg.tar.zst, tars, zip in dist/
├── dist/               # generated packages
├── lunuz-x86_64.AppImage
├── AppDir/             # AppImage source
├── org.davi.lunuz-tools.json
├── snapcraft.yaml
├── README.md           # this file (English)
├── README.pt-BR.md     # Portuguese
└── setup.py
~/bin/
├── lunuz               # Python wrapper
├── lunuz.sh            # shell script
├── lunuz-gui           # GUI launcher
└── lunuz-appimage.sh   # extracts/runs the AppImage without FUSE
```
