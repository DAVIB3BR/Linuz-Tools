#!/usr/bin/env python3
"""lunuz tools - Ações de sistema: drivers, repositórios, kernels,
otimização, saúde, rede e atualização.

Cada ação gera um script bash no momento do clique, adaptado à
distribuição detectada. Ações com root=True rodam via pkexec.
"""

import os
import re


# ------------------------------------------------------------------
# Detecção da distribuição
# ------------------------------------------------------------------
def detect_distro():
    """Retorna dict com id, name, version e family da distro."""
    info = {"id": "unknown", "name": "Unknown", "version": "", "family": "unknown"}
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            data = {}
            for line in fh:
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k] = v.strip().strip('"')
        info["id"] = data.get("ID", "unknown")
        info["name"] = data.get("NAME", info["id"])
        info["version"] = data.get("VERSION_ID", "")
        ids = [info["id"]] + data.get("ID_LIKE", "").split()
        if any(i in ("debian", "ubuntu", "linuxmint", "pop", "raspbian", "elementary") for i in ids):
            info["family"] = "debian"
        elif any(i in ("fedora", "rhel", "centos", "rocky", "almalinux", "nobara") for i in ids):
            info["family"] = "fedora"
        elif any(i in ("arch", "manjaro", "endeavouros", "cachyos", "garuda") for i in ids):
            info["family"] = "arch"
        elif any(i == "suse" or i.startswith("opensuse") or i == "sles" for i in ids):
            info["family"] = "suse"
    except OSError:
        pass
    return info


def pkg_install(packages, family=None):
    """Comando de instalação SEM sudo (os scripts rodam como root via pkexec)."""
    fam = family or detect_distro()["family"]
    pkgs = " ".join(packages)
    if fam == "debian":
        return "DEBIAN_FRONTEND=noninteractive apt install -y " + pkgs
    if fam == "fedora":
        return "dnf install -y " + pkgs
    if fam == "arch":
        return "pacman -S --noconfirm " + pkgs
    if fam == "suse":
        return "zypper --non-interactive install " + pkgs
    return "echo 'Distribuicao nao suportada para instalacao de pacotes'"


def _fam():
    return detect_distro()["family"]


# ==================================================================
# BUILDERS DE SCRIPTS (drivers)
# ==================================================================
def build_nvidia():
    d = detect_distro()
    if d["family"] == "debian":
        if "ubuntu" in d["id"] or "mint" in d["id"]:
            return (
                "set -e\n"
                "apt update\n"
                "apt install -y ubuntu-drivers-common\n"
                "ubuntu-drivers autoinstall\n"
                "echo 'Driver NVIDIA instalado. REINICIE o computador.'\n"
            )
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y firmware-misc-nonfree 2>/dev/null || true\n"
            "apt install -y nvidia-driver\n"
            "update-initramfs -u\n"
            "echo 'Driver NVIDIA instalado. REINICIE o computador.'\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf install -y 'https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm'\n"
            "dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda\n"
            "akmods --force\n"
            "dracut -f\n"
            "echo 'Driver NVIDIA (RPM Fusion) instalado. REINICIE o computador.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -Sy --noconfirm nvidia nvidia-utils lib32-nvidia-utils\n"
            "mkinitcpio -P\n"
            "echo 'Driver NVIDIA instalado. REINICIE o computador.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            ". /etc/os-release\n"
            "if ! zypper --non-interactive install nvidia-drivers; then\n"
            "  echo 'Adicionando repositorio NVIDIA oficial...'\n"
            "  zypper --non-interactive addrepo -f "
            "\"https://download.nvidia.com/opensuse/$VERSION_ID\" nvidia\n"
            "  zypper --non-interactive install nvidia-drivers\n"
            "fi\n"
            "echo 'Driver NVIDIA instalado. REINICIE o computador.'\n"
        )
    return "echo 'Distribuicao nao suportada para driver NVIDIA automatico'\n"


def build_nvidia_fix():
    """Corrige NVIDIA que nao inicia / tela preta / conflito com nouveau."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "echo '== Limpando instalacao anterior =='\n"
            "apt update\n"
            "apt install -y --reinstall nvidia-driver 2>/dev/null || apt install -y nvidia-driver\n"
            "echo '== Removendo xorg.conf problematico =='\n"
            "rm -f /etc/X11/xorg.conf /etc/X11/xorg.conf.d/90-nvidia.conf\n"
            "echo '== Atualizando initramfs =='\n"
            "update-initramfs -u\n"
            "echo 'Concluido. REINICIE. Se ainda falhar, instale o driver aberto (nouveau).'\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf remove -y akmod-nvidia 2>/dev/null || true\n"
            "dnf install -y akmod-nvidia\n"
            "akmods --force\n"
            "dracut -f\n"
            "echo 'Concluido. REINICIE o computador.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -S --noconfirm nvidia nvidia-utils\n"
            "mkinitcpio -P\n"
            "rm -f /etc/X11/xorg.conf.d/20-nvidia.conf\n"
            "echo 'Concluido. REINICIE o computador.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            "zypper --non-interactive install -f nvidia-drivers\n"
            "echo 'Concluido. REINICIE o computador.'\n"
        )
    return "echo 'Distribuicao nao suportada'\n"


def build_nouveau_restore():
    """Restaura o driver aberto nouveau (reversao segura da NVIDIA)."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt purge -y 'nvidia-*' 2>/dev/null || true\n"
            "apt install -y xserver-xorg-video-nouveau firmware-misc-nonfree || apt install -y xserver-xorg-video-nouveau\n"
            "rm -f /etc/modprobe.d/blacklist-nouveau.conf /etc/modprobe.d/blacklist.conf\n"
            "update-initramfs -u\n"
            "echo 'Driver aberto nouveau restaurado. REINICIE.'\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf remove -y akmod-nvidia xorg-x11-drv-nvidia 2>/dev/null || true\n"
            "dnf install -y xorg-x11-drv-nouveau\n"
            "dracut -f\n"
            "echo 'Driver aberto nouveau restaurado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -Rns --noconfirm nvidia nvidia-utils lib32-nvidia-utils 2>/dev/null || true\n"
            "pacman -S --noconfirm xf86-video-nouveau\n"
            "mkinitcpio -P\n"
            "echo 'Driver aberto nouveau restaurado. REINICIE.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            "zypper --non-interactive remove -u nvidia-drivers 2>/dev/null || true\n"
            "zypper --non-interactive install xf86-video-nouveau\n"
            "echo 'Driver aberto nouveau restaurado. REINICIE.'\n"
        )
    return "echo 'Distribuicao nao suportada'\n"


def build_amd():
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y firmware-amd-graphics mesa-vulkan-drivers mesa-utils "
            "xserver-xorg-video-amdgpu\n"
            "echo 'Driver AMD/Radeon (Mesa) atualizado. REINICIE.'\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf install -y mesa-dri-drivers mesa-vulkan-drivers "
            "xorg-x11-drv-amdgpu vulkan-tools\n"
            "echo 'Driver AMD/Radeon (Mesa) atualizado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -S --noconfirm mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon "
            "xf86-video-amdgpu\n"
            "echo 'Driver AMD/Radeon (Mesa) atualizado. REINICIE.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            "zypper --non-interactive install Mesa Mesa-dri Mesa-Vulkan amdvlk\n"
            "echo 'Driver AMD/Radeon (Mesa) atualizado. REINICIE.'\n"
        )
    return "echo 'Distribuicao nao suportada'\n"


def build_intel():
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y firmware-misc-nonfree mesa-vulkan-drivers mesa-utils "
            "xserver-xorg-video-intel intel-media-va-driver\n"
            "echo 'Driver Intel atualizado. REINICIE.'\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf install -y mesa-dri-drivers mesa-vulkan-drivers "
            "xorg-x11-drv-intel intel-media-driver\n"
            "echo 'Driver Intel atualizado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -S --noconfirm mesa lib32-mesa vulkan-intel lib32-vulkan-intel "
            "xf86-video-intel\n"
            "echo 'Driver Intel atualizado. REINICIE.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            "zypper --non-interactive install Mesa Mesa-dri intel-vaapi-driver\n"
            "echo 'Driver Intel atualizado. REINICIE.'\n"
        )
    return "echo 'Distribuicao nao suportada'\n"


def build_realtek_firmware():
    """Firmware Realtek (placas de rede/wifi integradas)."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y firmware-realtek firmware-linux-free || apt install -y firmware-linux\n"
            "echo 'Firmware Realtek instalado. REINICIE.'\n"
        )
    if d["family"] == "fedora":
        return "set -e\ndnf install -y linux-firmware\necho 'Firmware Realtek (linux-firmware) atualizado. REINICIE.'\n"
    if d["family"] == "arch":
        return "set -e\npacman -S --noconfirm linux-firmware\necho 'Firmware Realtek (linux-firmware) atualizado. REINICIE.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper --non-interactive install kernel-firmware-realtek 2>/dev/null || zypper --non-interactive install kernel-firmware\necho 'Firmware Realtek instalado. REINICIE.'\n"
    return "echo 'Distribuicao nao suportada'\n"


def build_realtek_wifi():
    """Driver Wi-Fi Realtek rtl88xxau (dkms) - o mais problemático."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y dkms git build-essential \"linux-headers-$(uname -r)\"\n"
            "rm -rf /tmp/rtl8812au\n"
            "git clone --depth=1 https://github.com/aircrack-ng/rtl8812au.git /tmp/rtl8812au\n"
            "cd /tmp/rtl8812au\n"
            "if make dkms_install; then\n"
            "  echo 'Driver rtl88xxau instalado via DKMS.'\n"
            "else\n"
            "  echo 'Falha no dkms_install - veja saida acima.'\n"
            "fi\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf install -y dkms git gcc make \"kernel-devel-$(uname -r)\" || dnf install -y dkms git gcc make kernel-devel\n"
            "rm -rf /tmp/rtl8812au\n"
            "git clone --depth=1 https://github.com/aircrack-ng/rtl8812au.git /tmp/rtl8812au\n"
            "cd /tmp/rtl8812au && make dkms_install || make install\n"
            "echo 'Driver rtl88xxau instalado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -S --noconfirm dkms git base-devel \"linux-headers\"\n"
            "rm -rf /tmp/rtl8812au\n"
            "git clone --depth=1 https://github.com/aircrack-ng/rtl8812au.git /tmp/rtl8812au\n"
            "cd /tmp/rtl8812au && make dkms_install\n"
            "echo 'Driver rtl88xxau instalado. REINICIE.'\n"
        )
    if d["family"] == "suse":
        return (
            "set -e\n"
            "zypper --non-interactive install dkms git gcc make kernel-devel\n"
            "rm -rf /tmp/rtl8812au\n"
            "git clone --depth=1 https://github.com/aircrack-ng/rtl8812au.git /tmp/rtl8812au\n"
            "cd /tmp/rtl8812au && make dkms_install\n"
            "echo 'Driver rtl88xxau instalado. REINICIE.'\n"
        )
    return "echo 'Distribuicao nao suportada'\n"


def build_acer():
    """Suporte a hardware Acer: acpid, acer-wmi, controle de fan."""
    return (
        "set -e\n"
        "echo '== Instalando ACPI (Acer) =='\n"
        + pkg_install(["acpid", "acpi"]) + "\n"
        "systemctl enable --now acpid 2>/dev/null || true\n"
        "echo 'acer-wmi' > /etc/modules-load.d/acer-wmi.conf\n"
        "modprobe acer-wmi 2>/dev/null || modprobe acerhdf 2>/dev/null || true\n"
        "echo '== Modulos Acer carregados =='\n"
        "lsmod | grep -i acer || echo '(nenhum modulo acer ativo - pode nao ser necessario)'\n"
        "echo 'Pronto. Verifique: dmesg | grep -i acer'\n"
    )


def build_firmware_update():
    """Atualiza todos os firmwares/drivers de hardware."""
    d = detect_distro()
    if d["family"] == "debian":
        return "set -e\napt update\napt install -y --only-upgrade linux-firmware firmware-linux-free 2>/dev/null || apt install -y linux-firmware\necho 'Firmware atualizado.'\n"
    if d["family"] == "fedora":
        return "set -e\ndnf upgrade -y linux-firmware\necho 'Firmware atualizado.'\n"
    if d["family"] == "arch":
        return "set -e\npacman -Sy --noconfirm linux-firmware\necho 'Firmware atualizado.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper --non-interactive update kernel-firmware\necho 'Firmware atualizado.'\n"
    return "echo 'Distribuicao nao suportada'\n"


# ==================================================================
# BUILDERS (repositórios)
# ==================================================================
def build_flatpak():
    return (
        "set -e\n"
        + pkg_install(["flatpak"]) + "\n"
        "flatpak remote-add --if-not-exists flathub "
        "https://dl.flathub.org/repo/flathub.flatpakrepo\n"
        "echo 'Flatpak + Flathub prontos.'\n"
    )


def build_snapd():
    d = detect_distro()
    base = {"debian": "apt install -y snapd",
            "fedora": "dnf install -y snapd",
            "arch": "pacman -S --noconfirm snapd",
            "suse": "zypper --non-interactive install snapd"}.get(d["family"])
    if not base:
        return "echo 'Distribuicao nao suportada'\n"
    return (
        "set -e\n"
        "apt update 2>/dev/null || pacman -Sy 2>/dev/null || true\n"
        + base + "\n"
        "systemctl enable --now snapd.socket 2>/dev/null || true\n"
        "systemctl enable --now snapd.apparmor 2>/dev/null || true\n"
        "[ -e /snap ] || ln -sf /var/lib/snapd/snap /snap\n"
        "echo 'snapd instalado. Faca logout/login para PATH do snap.'\n"
    )


def build_homebrew():
    # Instala como usuário normal (sem root)
    return (
        "set -e\n"
        "if command -v brew >/dev/null 2>&1; then\n"
        "  echo 'Homebrew ja instalado:'; brew --version\n"
        "  exit 0\n"
        "fi\n"
        "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
        "echo 'Homebrew instalado. Adicione ao PATH:'\n"
        "echo '  eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\"'\n"
    )


def build_nix():
    return (
        "set -e\n"
        "if command -v nix >/dev/null 2>&1; then\n"
        "  echo 'Nix ja instalado:'; nix --version\n"
        "  exit 0\n"
        "fi\n"
        "sh <(curl -L https://nixos.org/nix/install) --daemon\n"
        "echo 'Nix instalado. Faca login novamente para ativar.'\n"
    )


def build_pip():
    d = detect_distro()
    pkgs = {"debian": ["python3-pip", "python3-venv"],
            "fedora": ["python3-pip"],
            "arch": ["python", "python-pip"],
            "suse": ["python3-pip"]}.get(d["family"], ["python3-pip"])
    return (
        "set -e\n"
        + pkg_install(pkgs) + "\n"
        "python3 -m pip --version 2>/dev/null || python3 -m ensurepip --upgrade\n"
        "echo 'pip pronto.'\n"
    )


def build_nonfree_repos():
    """Habilita non-free/contrib (Debian/Ubuntu) - necessario p/ NVIDIA etc."""
    return (
        "set -e\n"
        "if [ ! -f /etc/debian_version ]; then\n"
        "  echo 'Esta acao e para Debian/Ubuntu (/etc/debian_version ausente).'\n"
        "  exit 0\n"
        "fi\n"
        "apt update\n"
        "# Debian 12+ (deb822)\n"
        "if [ -f /etc/apt/sources.list.d/debian.sources ]; then\n"
        "  sed -i 's/^Components: .*/Components: main contrib non-free non-free-firmware/' "
        "/etc/apt/sources.list.d/debian.sources\n"
        "fi\n"
        "# Debian classico\n"
        "if [ -f /etc/apt/sources.list ]; then\n"
        "  sed -i 's/ main$/ main contrib non-free non-free-firmware/; s/ main / main contrib non-free non-free-firmware /' "
        "/etc/apt/sources.list\n"
        "fi\n"
        "# Ubuntu\n"
        "if command -v add-apt-repository >/dev/null 2>&1; then\n"
        "  add-apt-repository -y contrib non-free non-free-firmware 2>/dev/null || true\n"
        "fi\n"
        "apt update\n"
        "echo 'Repositorios non-free/contrib habilitados.'\n"
    )


def build_rpmfusion():
    return (
        "set -e\n"
        "if [ ! -f /etc/fedora-release ] && [ ! -f /etc/redhat-release ]; then\n"
        "  echo 'Esta acao e para Fedora/RHEL.'\n"
        "  exit 0\n"
        "fi\n"
        "dnf install -y 'https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm' "
        "'https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm'\n"
        "echo 'RPM Fusion habilitado.'\n"
    )


def build_multilib():
    return (
        "set -e\n"
        "if ! command -v pacman >/dev/null 2>&1; then\n"
        "  echo 'Esta acao e para Arch/Manjaro.'\n"
        "  exit 0\n"
        "fi\n"
        "grep -q '^\\[multilib\\]' /etc/pacman.conf || "
        "sed -i '/^#\\[multilib\\]/,/^#Include/ s/^#//' /etc/pacman.conf\n"
        "pacman -Sy\n"
        "echo 'Repositorio multilib habilitado.'\n"
    )


def build_packman():
    return (
        "set -e\n"
        "if ! command -v zypper >/dev/null 2>&1; then\n"
        "  echo 'Esta acao e para openSUSE.'\n"
        "  exit 0\n"
        "fi\n"
        ". /etc/os-release\n"
        "zypper addrepo -cfp 90 "
        "\"https://packman.inode.at/suse/openSUSE_${VERSION_ID}/\" packman || true\n"
        "zypper refresh\n"
        "echo 'Repositorio Packman habilitado.'\n"
    )


def build_repo_refresh():
    return (
        "set -e\n"
        "if command -v apt-get >/dev/null 2>&1; then apt update\n"
        "elif command -v dnf >/dev/null 2>&1; then dnf makecache\n"
        "elif command -v pacman >/dev/null 2>&1; then pacman -Sy\n"
        "elif command -v zypper >/dev/null 2>&1; then zypper refresh\n"
        "else echo 'Gerenciador de pacotes nao reconhecido'; fi\n"
        "echo 'Cache de repositorios atualizado.'\n"
    )


# ==================================================================
# BUILDERS (kernels)
# ==================================================================
def build_kernel_default():
    d = detect_distro()
    if d["family"] == "debian":
        pkg = "linux-image-generic" if "ubuntu" in d["id"] else "linux-image-amd64"
        return f"set -e\napt update\napt install -y {pkg}\necho 'Kernel padrao instalado. REINICIE.'\n"
    if d["family"] == "fedora":
        return "set -e\ndnf install -y kernel\necho 'Kernel instalado. REINICIE.'\n"
    if d["family"] == "arch":
        return "set -e\npacman -S --noconfirm linux linux-headers\necho 'Kernel instalado. REINICIE.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper --non-interactive install kernel-default\necho 'Kernel instalado. REINICIE.'\n"
    return "echo 'Distribuicao nao suportada'\n"


def build_kernel_lts():
    d = detect_distro()
    if d["family"] == "debian":
        pkg = "linux-image-generic" if "ubuntu" in d["id"] else "linux-image-amd64"
        return (
            f"set -e\napt update\napt install -y {pkg}\n"
            "echo 'Nota: o kernel padrao do Debian/Ubuntu ja e uma serie LTS.'\n"
            "echo 'Kernel LTS instalado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return "set -e\npacman -S --noconfirm linux-lts linux-lts-headers\necho 'Kernel LTS instalado. REINICIE.'\n"
    if d["family"] == "fedora":
        return "echo 'Fedora nao publica LTS - use o kernel principal ou o XanMod.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper --non-interactive install kernel-default\necho 'openSUSE: kernel-default e o recomendado. REINICIE.'\n"
    return "echo 'Distribuicao nao suportada'\n"


def build_kernel_zen():
    d = detect_distro()
    if d["family"] == "arch":
        return "set -e\npacman -S --noconfirm linux-zen linux-zen-headers\necho 'Kernel Zen instalado. REINICIE.'\n"
    if d["family"] == "debian":
        return (
            "echo 'Kernel Zen nao e publicado para Debian/Ubuntu.'\n"
            "echo 'Alternativa similar: instale o XanMod (menu Kernels Linux).'\n"
        )
    if d["family"] == "fedora":
        return "echo 'Kernel Zen nao e publicado para Fedora. Alternativa: XanMod (via site).'\n"
    return "echo 'Indisponivel para esta distro'\n"


def build_kernel_xanmod():
    """XanMod - kernel modificado (scheduler xanmod, precacao, bbsched)."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y wget gpg\n"
            "wget -qO- https://dl.xanmod.org/gpg.key | gpg --dearmor -o /usr/share/keyrings/xanmod-archive-keyring.gpg\n"
            "echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://dl.xanmod.org/repo deb main' "
            "> /etc/apt/sources.list.d/xanmod.list\n"
            "apt update\n"
            "(apt install -y linux-xanmod-x64v3 || apt install -y linux-xanmod-x64v2 || apt install -y linux-xanmod-x64v1)\n"
            "echo 'Kernel XanMod instalado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "set -e\n"
            "pacman -S --noconfirm git base-devel\n"
            "rm -rf /tmp/chaotic-aur\n"
            "mkdir -p /etc/pacman.d/keys\n"
            "pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com || true\n"
            "pacman-key --lsign-key 3056513887B78AEB || true\n"
            "grep -q chaotic-aur /etc/pacman.conf || "
            "echo '[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist' >> /etc/pacman.conf\n"
            "echo 'Repo chaotic-aur habilitado (pacote linux-xanmod a partir do AUR).' \n"
            "pacman -Sy\n"
            "echo 'Instale pelo AUR: paru -S linux-xanmod (se tiver um AUR helper).'\n"
        )
    return (
        "echo 'XanMod oficial suporta Debian/Ubuntu.'\n"
        "echo 'Para Fedora/Arch/openSUSE baixe manualmente: https://xanmod.org'\n"
    )


def build_kernel_liquorix():
    """Liquorix - kernel modificado focado em gaming/desempenho."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y curl gpg\n"
            "curl -fsSL 'https://deb.liquorix.net/linux-liquorix.gpg' | "
            "gpg --dearmor -o /etc/apt/trusted.gpg.d/liquorix.gpg\n"
            "CODENAME=$(. /etc/os-release && echo \"$VERSION_CODENAME\")\n"
            "echo \"deb https://deb.liquorix.net/ $CODENAME main\" > /etc/apt/sources.list.d/liquorix.list\n"
            "apt update\n"
            "apt install -y liquorix-generic\n"
            "echo 'Kernel Liquorix instalado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return (
            "echo 'Liquorix no Arch: use o AUR (liquorix-rt ou liquorix):'\n"
            "echo '  paru -S liquorix   (requer helper AUR)'\n"
            "echo 'Docs: https://liquorix.net'\n"
        )
    return "echo 'Liquorix oficial suporta Debian/Ubuntu. Baixe: https://liquorix.net'\n"


def build_kernel_rt():
    """Kernel de tempo real (RT)."""
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update\n"
            "apt install -y linux-image-rt-amd64 || "
            "echo 'Pacote linux-image-rt indisponivel nesta versao do Debian.'\n"
            "echo 'Kernel RT instalado. REINICIE.'\n"
        )
    if d["family"] == "arch":
        return "set -e\npacman -S --noconfirm linux-rt linux-rt-headers\necho 'Kernel RT instalado. REINICIE.'\n"
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf copr enable -y syzdalsky/rt || true\n"
            "dnf install -y kernel-rt 2>/dev/null || "
            "echo 'kernel-rt nao disponivel. Habilite updates-realtime: https://fedoraproject.org/wiki/Changes/Kernel_RT'\n"
        )
    return "echo 'Indisponivel para esta distro'\n"


def build_kernel_download():
    """Baixa o tarball mainline do kernel.org para ~/Downloads (sem root)."""
    return (
        "set -e\n"
        "echo 'Consultando kernel.org...'\n"
        "if command -v curl >/dev/null 2>&1; then DL='curl -fsSL'; DL2='curl -fLO';\n"
        "elif command -v wget >/dev/null 2>&1; then DL='wget -qO-'; DL2='wget';\n"
        "else echo 'Instale curl ou wget.'; exit 1; fi\n"
        "VER=$($DL https://www.kernel.org/releases.json | "
        "grep -o '\"version\":\"[^\"]*\"' | head -1 | cut -d'\"' -f4)\n"
        "if [ -z \"$VER\" ]; then\n"
        "  VER=$($DL https://www.kernel.org | grep -oE 'linux-[0-9]+\\.[0-9]+(\\.[0-9]+)?\\.tar\\.xz' | "
        "head -1 | sed 's/linux-//;s/\\.tar\\.xz//')\n"
        "fi\n"
        "[ -n \"$VER\" ] || { echo 'Nao foi possivel obter a versao.'; exit 1; }\n"
        "MAJ=${VER%%.*}\n"
        "mkdir -p \"$HOME/Downloads\"\n"
        "cd \"$HOME/Downloads\"\n"
        "echo \"Baixando linux-$VER.tar.xz (kernel mainline)...\"\n"
        "$DL2 \"https://cdn.kernel.org/pub/linux/kernel/v$MAJ.x/linux-$VER.tar.xz\" || exit 1\n"
        "echo \"Salvo em $HOME/Downloads/linux-$VER.tar.xz\"\n"
        "echo 'Para compilar: descompacte e rode: make menuconfig && make -j$(nproc)'\n"
    )


def build_kernel_list():
    return (
        "echo '== Kernel em execucao =='\n"
        "uname -r\n"
        "echo\n"
        "echo '== Pacotes de kernel instalados =='\n"
        "if command -v dpkg >/dev/null 2>&1; then dpkg -l 'linux-image*' 2>/dev/null | grep '^ii'\n"
        "elif command -v pacman >/dev/null 2>&1; then pacman -Q | grep -E '^linux' || true\n"
        "elif command -v rpm >/dev/null 2>&1; then rpm -q kernel 2>/dev/null || true\n"
        "elif command -v zypper >/dev/null 2>&1; then zypper se -i kernel 2>/dev/null | grep -i '^i' || true\n"
        "fi\n"
        "echo\n"
        "echo '== Entradas do GRUB (kernels disponiveis no boot) =='\n"
        "grep -E '^menuentry |^submenu ' /boot/grub/grub.cfg 2>/dev/null | head -20 || "
        "grep '^menuentry' /boot/grub2/grub.cfg 2>/dev/null | head -20 || echo '(grub nao encontrado)'\n"
    )


def build_kernel_remove_old():
    d = detect_distro()
    if d["family"] == "debian":
        return "set -e\napt autoremove --purge -y\necho 'Kernels antigos removidos (o atual e mantido).'\n"
    if d["family"] == "arch":
        return "set -e\npacman -Qtdq | xargs -r pacman -Rns --noconfirm\necho 'Pacotes orfaos removidos.'\n"
    if d["family"] == "fedora":
        return "set -e\ndnf autoremove -y\necho 'Pacotes orfaos removidos.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper purge -u\necho 'Pacotes orfaos removidos.'\n"
    return "echo 'Distribuicao nao suportada'\n"


# ==================================================================
# BUILDERS (otimização)
# ==================================================================
SCRIPT_OPTIMIZE = (
    "set -e\n"
    "echo '== 1/5 Swappiness =='\n"
    "sysctl -w vm.swappiness=10 vm.vfs_cache_pressure=50\n"
    "printf 'vm.swappiness=10\\nvm.vfs_cache_pressure=50\\n' > /etc/sysctl.d/99-lunuz-tuning.conf\n"
    "echo '== 2/5 TRIM (SSD) =='\n"
    "systemctl enable --now fstrim.timer 2>/dev/null || true\n"
    "echo '== 3/5 Log do systemd (limite 200M) =='\n"
    "mkdir -p /etc/systemd/journald.conf.d\n"
    "printf '[Journal]\\nSystemMaxUse=200M\\n' > /etc/systemd/journald.conf.d/lunuz.conf\n"
    "systemctl restart systemd-journald 2>/dev/null || true\n"
    "journalctl --vacuum-size=200M >/dev/null 2>&1 || true\n"
    "echo '== 4/5 Cache de pacotes =='\n"
    "if command -v apt-get >/dev/null 2>&1; then apt-get clean\n"
    "elif command -v dnf >/dev/null 2>&1; then dnf clean all >/dev/null\n"
    "elif command -v pacman >/dev/null 2>&1; then rm -rf /var/cache/pacman/pkg/*.pkg.tar.*\n"
    "elif command -v zypper >/dev/null 2>&1; then zypper clean\n"
    "fi\n"
    "echo '== 5/5 Concluido =='\n"
    "echo 'Otimizacao aplicada com sucesso.'\n"
)

SCRIPT_ZRAM = (
    "set -e\n"
    "echo '== Habilitando ZRAM (memoria comprimida) =='\n"
    "modprobe zram 2>/dev/null || true\n"
    "if [ ! -e /dev/zram0 ]; then\n"
    "  echo 'ZRAM nao disponivel neste kernel.'\n"
    "  exit 0\n"
    "fi\n"
    "swapoff /dev/zram0 2>/dev/null || true\n"
    "echo lz4 > /sys/block/zram0/comp_algorithm 2>/dev/null || true\n"
    "RAM_TOTAL=$(awk '/MemTotal/{print $2}' /proc/meminfo)\n"
    "ZSIZE=$(( RAM_TOTAL / 2 ))k\n"
    "echo \"$ZSIZE\" > /sys/block/zram0/disksize\n"
    "mkswap /dev/zram0 >/dev/null\n"
    "swapon -p 100 /dev/zram0\n"
    "echo 'ZRAM ativo:'\n"
    "swapon --show\n"
    "echo '(Volatil - configure zram-tools para persistir entre reinicios)'\n"
)

SCRIPT_SWAPPINESS = (
    "set -e\n"
    "sysctl -w vm.swappiness=10\n"
    "printf 'vm.swappiness=10\\n' > /etc/sysctl.d/99-lunuz-swappiness.conf\n"
    "echo 'Swappiness definido como 10 (menos uso de swap, mais RAM).'\n"
)

SCRIPT_TRIM = (
    "set -e\n"
    "systemctl enable --now fstrim.timer\n"
    "echo 'TRIM semanal habilitado:'\n"
    "systemctl list-timers fstrim.timer --no-pager | head -5\n"
)

SCRIPT_CLEAN = (
    "set -e\n"
    "echo '== Logs =='\n"
    "journalctl --vacuum-size=200M || true\n"
    "echo '== Cache de pacotes =='\n"
    "if command -v apt-get >/dev/null 2>&1; then apt-get clean; apt-get autoremove -y\n"
    "elif command -v dnf >/dev/null 2>&1; then dnf clean all\n"
    "elif command -v pacman >/dev/null 2>&1; then pacman -Scc --noconfirm\n"
    "elif command -v zypper >/dev/null 2>&1; then zypper clean\n"
    "fi\n"
    "echo 'Espaco liberado:'\n"
    "df -h / | tail -1\n"
)

SCRIPT_MAKEFLAGS = (
    "set -e\n"
    "N=$(nproc)\n"
    "echo \"Habilitando compilacao paralela: MAKEFLAGS=-j$N\"\n"
    "if [ -f /etc/environment ]; then\n"
    "  grep -q '^MAKEFLAGS=' /etc/environment && "
    "sed -i \"s|^MAKEFLAGS=.*|MAKEFLAGS=\\\"-j$N\\\"|\" /etc/environment || "
    "echo \"MAKEFLAGS=\\\"-j$N\\\"\" >> /etc/environment\n"
    "fi\n"
    "if [ -f /etc/makepkg.conf ]; then\n"
    "  sed -i \"s|^#MAKEFLAGS=.*|MAKEFLAGS=\\\"-j$N\\\"|\" /etc/makepkg.conf\n"
    "fi\n"
    "echo 'Pronto (aplica em novos terminais/compilacoes).'\n"
)

SCRIPT_BOOT = (
    "echo '== Tempo de boot =='\n"
    "systemd-analyze 2>/dev/null || true\n"
    "echo\n"
    "echo '== Top 15 servicos mais lentos =='\n"
    "systemd-analyze blame 2>/dev/null | head -15 || true\n"
    "echo\n"
    "echo '== Servicos com falha =='\n"
    "systemctl --failed --no-pager 2>/dev/null || true\n"
)


# ==================================================================
# BUILDERS (atualização do sistema)
# ==================================================================
def build_full_update():
    d = detect_distro()
    if d["family"] == "debian":
        return "set -e\napt update\napt upgrade -y\necho 'Sistema atualizado.'\n"
    if d["family"] == "fedora":
        return "set -e\ndnf upgrade -y --refresh\necho 'Sistema atualizado.'\n"
    if d["family"] == "arch":
        return "set -e\npacman -Syu --noconfirm\necho 'Sistema atualizado.'\n"
    if d["family"] == "suse":
        return "set -e\nzypper --non-interactive update\necho 'Sistema atualizado.'\n"
    return "echo 'Distribuicao nao suportada'\n"


def build_flatpak_update():
    return (
        "set -e\n"
        "command -v flatpak >/dev/null 2>&1 || { echo 'Flatpak nao instalado (menu Repositorios).'; exit 1; }\n"
        "flatpak update -y\n"
        "echo 'Flatpaks atualizados.'\n"
    )


def build_snap_update():
    return (
        "set -e\n"
        "command -v snap >/dev/null 2>&1 || { echo 'snapd nao instalado (menu Repositorios).'; exit 1; }\n"
        "snap refresh\n"
        "echo 'Snaps atualizados.'\n"
    )


# ==================================================================
# BUILDERS (rede)
# ==================================================================
SCRIPT_NET_STATUS = (
    "echo '== Interfaces de rede =='\n"
    "(ip -br addr 2>/dev/null || ifconfig -a 2>/dev/null || echo 'ip/ifconfig ausente')\n"
    "echo\n"
    "echo '== Rota padrao =='\n"
    "(ip route 2>/dev/null || route -n 2>/dev/null || true)\n"
    "echo\n"
    "echo '== DNS =='\n"
    "cat /etc/resolv.conf 2>/dev/null | grep -v '^#' | head -5\n"
    "echo\n"
    "echo '== Conexao (ping 1.1.1.1) =='\n"
    "ping -c 3 -W 2 1.1.1.1 2>/dev/null || echo 'Sem resposta - sem internet?' \n"
)

SCRIPT_WIFI = (
    "echo '== Redes Wi-Fi =='\n"
    "if command -v nmcli >/dev/null 2>&1; then\n"
    "  nmcli device wifi list 2>/dev/null || nmcli radio wifi on\n"
    "elif command -v iwctl >/dev/null 2>&1; then\n"
    "  iwctl station list\n"
    "elif command -v iw >/dev/null 2>&1; then\n"
    "  iw dev | grep -E 'Interface|ssid' \n"
    "else echo 'nmcli/iwctl nao encontrados (instale network-manager).'; fi\n"
)

SCRIPT_FIREWALL = (
    "echo '== Firewall =='\n"
    "if command -v ufw >/dev/null 2>&1; then ufw status verbose\n"
    "elif command -v firewall-cmd >/dev/null 2>&1; then firewall-cmd --state && firewall-cmd --list-all\n"
    "elif command -v nft >/dev/null 2>&1; then nft list ruleset | head -30\n"
    "else echo 'Nenhum firewall ativo detectado (ufw/firewalld/nft).'; fi\n"
)

SCRIPT_DNS_FIX = (
    "set -e\n"
    "echo '== Testando DNS =='\n"
    "for s in 1.1.1.1 8.8.8.8 9.9.9.9; do\n"
    "  printf '%s: ' \"$s\"\n"
    "  (timeout 2 getent hosts kernel.org >/dev/null 2>&1 && echo OK) || echo falhou\n"
    "done\n"
    "echo\n"
    "echo '== Configurando DNS rapido (Cloudflare + Google) =='\n"
    "mkdir -p /etc/systemd/resolved.conf.d\n"
    "printf '[Resolve]\\nDNS=1.1.1.1 8.8.8.8\\nDomains=~.\\n' > /etc/systemd/resolved.conf.d/lunuz.conf\n"
    "systemctl restart systemd-resolved 2>/dev/null || true\n"
    "resolvectl flush-caches 2>/dev/null || true\n"
    "echo 'DNS definido: 1.1.1.1 / 8.8.8.8'\n"
)


# ==================================================================
# BUILDERS (saúde - somente leitura)
# ==================================================================
SCRIPT_DISK = (
    "echo '== Espaco em disco =='\n"
    "df -hT -x tmpfs -x devtmpfs -x squashfs 2>/dev/null || df -h\n"
)

SCRIPT_RAM = (
    "echo '== Memoria RAM =='\n"
    "free -h\n"
    "echo\n"
    "echo '== Swap =='\n"
    "swapon --show 2>/dev/null || cat /proc/swaps\n"
)

SCRIPT_TEMP = (
    "echo '== Temperatura =='\n"
    "if command -v sensors >/dev/null 2>&1; then\n"
    "  sensors 2>/dev/null | grep -Ei 'temp|core' || sensors\n"
    "else\n"
    "  for z in /sys/class/thermal/thermal_zone*/; do\n"
    "    [ -f \"$z/temp\" ] || continue\n"
    "    T=$(cat \"$z/temp\" 2>/dev/null)\n"
    "    NAME=$(cat \"$z/type\" 2>/dev/null)\n"
    "    [ -n \"$T\" ] && echo \"$NAME: $(( T / 1000 )) C\"\n"
    "  done\n"
    "fi\n"
)

SCRIPT_FAILED_UNITS = (
    "echo '== Unidades systemd com falha =='\n"
    "systemctl --failed --no-pager 2>/dev/null || echo 'systemd indisponivel'\n"
    "echo\n"
    "echo '== Ultimos erros do journal =='\n"
    "journalctl -p err -b --no-pager 2>/dev/null | tail -25 || true\n"
)

SCRIPT_UPDATES_PENDING = (
    "echo '== Atualizacoes pendentes =='\n"
    "if command -v apt-get >/dev/null 2>&1; then\n"
    "  apt list --upgradable 2>/dev/null | head -40\n"
    "elif command -v dnf >/dev/null 2>&1; then\n"
    "  dnf check-update 2>/dev/null | head -40 || true\n"
    "elif command -v pacman >/dev/null 2>&1; then\n"
    "  pacman -Qu 2>/dev/null | head -40 || echo 'rode: pacman -Syu'\n"
    "elif command -v zypper >/dev/null 2>&1; then\n"
    "  zypper list-updates 2>/dev/null | head -40\n"
    "fi\n"
)

SCRIPT_SMART = (
    "set -e\n"
    "command -v smartctl >/dev/null 2>&1 || { echo 'Instale smartmontools (menu Repositorios).'; exit 1; }\n"
    "for d in /dev/sd[a-z] /dev/nvme[0-9]n[0-9] /dev/mmcblk[0-9]; do\n"
    "  [ -b \"$d\" ] || continue\n"
    "  echo \"== $d ==\"\n"
    "  smartctl -H \"$d\" 2>/dev/null | grep -Ei 'result|overall' || true\n"
    "  smartctl -A \"$d\" 2>/dev/null | grep -Ei 'Model|Capacity|Power_On|Temperature|Reallocated|Wear' || true\n"
    "  echo\n"
    "done\n"
)

SCRIPT_HEALTH_REPORT = (
    "echo '================ RELATORIO lunuz tools ================'\n"
    "echo \"Data: $(date)\"\n"
    "echo \"Kernel: $(uname -r)\"\n"
    "echo\n"
    "echo '--- Disco ---'\n"
    "df -hT -x tmpfs -x devtmpfs -x squashfs 2>/dev/null | head -10\n"
    "echo\n"
    "echo '--- Memoria ---'\n"
    "free -h\n"
    "echo\n"
    "echo '--- Carga / Uptime ---'\n"
    "uptime\n"
    "echo\n"
    "echo '--- Unidades com falha ---'\n"
    "systemctl --failed --no-pager 2>/dev/null | head -10 || true\n"
    "echo\n"
    "echo '--- Top processos (CPU) ---'\n"
    "ps aux --sort=-%cpu 2>/dev/null | head -6 || true\n"
    "echo\n"
    "echo '======================================================='\n"
)

SCRIPT_HARDWARE_DETECT = (
    "echo '== Placa de video / GPU =='\n"
    "(lspci 2>/dev/null | grep -Ei 'vga|3d|display') || echo 'lspci ausente (instale pciutils)'\n"
    "echo\n"
    "echo '== Rede / Wi-Fi =='\n"
    "(lspci 2>/dev/null | grep -Ei 'network|ethernet') || true\n"
    "echo\n"
    "echo '== Audio =='\n"
    "(lspci 2>/dev/null | grep -i audio) || true\n"
    "echo\n"
    "echo '== USB =='\n"
    "(lsusb 2>/dev/null | head -15) || true\n"
    "echo\n"
    "echo '== Modulos carregados (drivers ativos) =='\n"
    "lsmod 2>/dev/null | head -15 || true\n"
    "echo\n"
    "echo '== Nome do hardware =='\n"
    "cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null || true\n"
    "cat /sys/class/dmi/id/board_vendor 2>/dev/null || true\n"
)




def build_toolchain_install():
    d = detect_distro()
    if d["family"] == "debian":
        pkgs = "default-jdk g++ python3 python3-pip nodejs npm make git"
    elif d["family"] == "fedora":
        pkgs = "java-21-openjdk-devel gcc-c++ python3 python3-pip nodejs npm make git"
    elif d["family"] == "arch":
        pkgs = "jdk-openjdk gcc python python-pip nodejs npm make git"
    elif d["family"] == "suse":
        pkgs = "java-21-openjdk-devel gcc-c++ python3 python3-pip nodejs npm make git"
    else:
        return "echo 'Distribuicao nao suportada'\n"
    return (
        "set -e\n"
        "apt update 2>/dev/null || pacman -Sy 2>/dev/null || dnf makecache 2>/dev/null || true\n"
        + pkg_install(pkgs.split()) + "\n"
        "echo '== Versoes instaladas =='\n"
        "java -version 2>&1 | head -1 || true\n"
        "g++ --version | head -1 || true\n"
        "python3 --version || true\n"
        "node --version || true\n"
        "echo 'Toolchains prontas.'\n"
    )


# ==================================================================
# BUILDERS - IDEs, editores, IA, ferramentas e linguagens
# ==================================================================
def _ensure_flatpak():
    """Garante flatpak + Flathub instalados (bootstrap por distro)."""
    return (
        "if ! command -v flatpak >/dev/null 2>&1; then\n"
        "  apt update 2>/dev/null || pacman -Sy 2>/dev/null || dnf makecache 2>/dev/null || zypper refresh 2>/dev/null || true\n"
        "  " + pkg_install(["flatpak"]) + "\n"
        "fi\n"
        "flatpak remote-add --if-not-exists flathub "
        "https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true\n"
    )


def build_flatpak_app(app_id, label):
    """Instala um aplicativo do Flathub com bootstrap do flatpak."""
    return (
        "set -e\n"
        + _ensure_flatpak()
        + f"flatpak install -y flathub {app_id}\n"
        + f"echo '{label} instalado via Flatpak.'\n"
        + f"flatpak info {app_id} 2>/dev/null | head -3 || true\n"
    )


def build_vscode():
    """Visual Studio Code: Flatpak primeiro, senão repositório Microsoft."""
    d = detect_distro()
    head = (
        "set -e\n"
        "if command -v flatpak >/dev/null 2>&1; then\n"
        "  flatpak remote-add --if-not-exists flathub "
        "https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true\n"
        "  if flatpak install -y flathub com.visualstudio.code; then\n"
        "    echo 'VS Code instalado via Flatpak.'\n"
        "    exit 0\n"
        "  fi\n"
        "fi\n"
    )
    if d["family"] == "debian":
        body = (
            "apt install -y wget gpg ca-certificates\n"
            "wget -qO- https://packages.microsoft.com/keys/microsoft.asc "
            "| gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg\n"
            "echo 'deb [arch=amd64] https://packages.microsoft.com/repos/code stable main' "
            "> /etc/apt/sources.list.d/vscode.list\n"
            "apt update && apt install -y code\n"
        )
    elif d["family"] == "fedora":
        body = (
            "rpm --import https://packages.microsoft.com/keys/microsoft.asc\n"
            "cat > /etc/yum.repos.d/vscode.repo <<'EOF'\n"
            "[code]\nname=Visual Studio Code\n"
            "baseurl=https://packages.microsoft.com/yumrepos/vscode\n"
            "enabled=1\ngpgcheck=1\n"
            "gpgkey=https://packages.microsoft.com/keys/microsoft.asc\nEOF\n"
            "dnf install -y code\n"
        )
    elif d["family"] == "suse":
        body = (
            "zypper --non-interactive install ca-certificates wget gpg2\n"
            "zypper --non-interactive addrepo "
            "https://packages.microsoft.com/repos/vscode/openSUSE_15/ vscode || true\n"
            "zypper --non-interactive refresh vscode\n"
            "zypper --non-interactive install code\n"
        )
    elif d["family"] == "arch":
        body = (
            "pacman -S --noconfirm --needed flatpak\n"
            "flatpak remote-add --if-not-exists flathub "
            "https://dl.flathub.org/repo/flathub.flatpakrepo\n"
            "flatpak install -y flathub com.visualstudio.code\n"
        )
    else:
        return "echo 'Distribuicao nao suportada para VS Code'\n"
    return head + body + "echo 'VS Code instalado.'\ncommand -v code >/dev/null && code --version | head -1 || true\n"


def build_sublime():
    """Sublime Text pelos repositórios oficiais."""
    d = detect_distro()
    if d["family"] == "debian":
        body = (
            "apt install -y curl ca-certificates gnupg\n"
            "curl -fsSL https://download.sublimetext.com/sublimehq-pub.gpg "
            "| gpg --dearmor > /etc/apt/trusted.gpg.d/sublimehq-archive.gpg\n"
            "[ -f /etc/apt/sources.list.d/sublime-text.list ] || "
            "echo 'deb https://download.sublimetext.com/ apt/stable/' "
            "> /etc/apt/sources.list.d/sublime-text.list\n"
            "apt update && apt install -y sublime-text\n"
        )
    elif d["family"] == "fedora":
        body = (
            "curl -fsSL https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo "
            "-o /etc/yum.repos.d/sublime-text.repo\n"
            "dnf install -y sublime-text\n"
        )
    elif d["family"] == "suse":
        body = (
            "zypper --non-interactive addrepo "
            "https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo sublime-text || true\n"
            "zypper --non-interactive refresh sublime-text\n"
            "zypper --non-interactive install sublime-text\n"
        )
    elif d["family"] == "arch":
        body = (
            "pacman -S --noconfirm --needed curl gnupg\n"
            "mkdir -p /etc/pacman.d/gnupg\n"
            "curl -fsSL https://download.sublimetext.com/sublimehq-pub.gpg "
            "| gpg --dearmor > /etc/pacman.d/gnupg/sublimehq-pacmand.gpg\n"
            "grep -q '\\[sublimehq-pacman\\]' /etc/pacman.conf || "
            "{ echo ''; echo '[sublimehq-pacman]'; "
            "echo 'SigLevel = Optional TrustAll'; "
            "echo 'Include = /etc/pacman.d/gnupg/sublimehq-pacmand.gpg'; } >> /etc/pacman.conf\n"
            "pacman -Sy --noconfirm sublime-text\n"
        )
    else:
        return "echo 'Distribuicao nao suportada para Sublime Text'\n"
    return "set -e\n" + body + "echo 'Sublime Text instalado.'\ncommand -v subl >/dev/null && subl --version || true\n"


def build_zed():
    """Zed (editor moderno) - instalador oficial, nivel de usuario."""
    return (
        "set -e\n"
        "curl -fsSL https://zed.dev/install.sh | ZED_EDITOR_UNATTENDED=1 sh\n"
        "echo 'Zed instalado. Caminho: ~/.local/bin/zed (ou 'zed' se ja estiver no PATH)'\n"
    )


def build_pkg(names, verify=None, refresh=True):
    """Script simples de instalacao via gerenciador da distro."""
    s = "set -e\n"
    if refresh:
        s += ("apt update 2>/dev/null || pacman -Sy 2>/dev/null || "
              "dnf makecache 2>/dev/null || zypper refresh 2>/dev/null || true\n")
    s += pkg_install(names) + "\n"
    if verify:
        s += "echo '== Verificacao =='\n" + verify + " || true\n"
    return s


def build_essential_tools():
    """Ferramentas de linha de comando essenciais (git, gh, htop...)."""
    base = ["git", "wget", "curl", "htop", "btop", "jq", "ripgrep", "fzf", "tmux", "unzip"]
    full = base + ["gh"]
    return (
        "set -e\n"
        + pkg_install(full) + " || " + pkg_install(base) + "\n"
        "echo '== Versoes =='\n"
        "git --version | head -1 || true\n"
        "curl --version | head -1 || true\n"
        "htop --version 2>/dev/null | head -1 || true\n"
        "echo 'Ferramentas prontas.'\n"
    )


def build_docker():
    """Docker Engine pelo script oficial (auto-detecta a distro)."""
    return (
        "set -e\n"
        "curl -fsSL https://get.docker.com | sh\n"
        "systemctl enable --now docker 2>/dev/null || true\n"
        "echo 'Docker instalado. Teste: docker run hello-world'\n"
        "docker --version || true\n"
    )


def build_ollama():
    """Ollama -LLM local (instalador oficial, nivel de usuario)."""
    return (
        "set -e\n"
        "curl -fsSL https://ollama.com/install.sh | sh\n"
        "echo 'Ollama instalado. Inicie com: ollama serve'\n"
        "ollama --version 2>/dev/null || true\n"
    )


def build_aider():
    """Aider - agente de IA para codificacao (pipx, nivel de usuario)."""
    return (
        "set -e\n"
        "if ! command -v pipx >/dev/null 2>&1; then\n"
        "  echo 'pipx nao encontrado - instalando...'\n"
        "  if [ \"$(id -u)\" = 0 ]; then\n"
        "    " + pkg_install(["pipx"]) + "\n"
        "  elif command -v sudo >/dev/null 2>&1; then\n"
        "    sudo " + pkg_install(["pipx"]) + "\n"
        "  elif command -v pkexec >/dev/null 2>&1; then\n"
        "    pkexec " + pkg_install(["pipx"]) + "\n"
        "  else\n"
        "    " + pkg_install(["pipx"]) + " || true\n"
        "  fi\n"
        "fi\n"
        "pipx install aider-chat || "
        "python3 -m pip install --user --break-system-packages aider-chat\n"
        "echo 'Aider instalado. Abra um novo terminal e digite: aider'\n"
    )


def build_npm_agent(pkg, name, bin_name):
    """Agente de IA distribuido via npm (requer Node.js)."""
    return (
        "set -e\n"
        "if ! command -v npm >/dev/null 2>&1; then\n"
        "  echo 'Node.js/npm nao encontrado - instalando...'\n"
        + pkg_install(["nodejs", "npm"]) + "\n"
        "fi\n"
        "npm install -g " + pkg + "\n"
        f"echo '{name} instalado. Use: {bin_name}'\n"
        f"command -v {bin_name} >/dev/null && {bin_name} --version 2>/dev/null | head -1 || true\n"
    )


def build_python_lang():
    d = detect_distro()
    if d["family"] == "debian":
        pkgs = ["python3", "python3-pip", "python3-venv"]
    elif d["family"] == "fedora":
        pkgs = ["python3", "python3-pip"]
    elif d["family"] == "arch":
        pkgs = ["python", "python-pip"]
    else:
        pkgs = ["python3", "python3-pip"]
    return build_pkg(pkgs, verify="python3 --version\npython3 -m pip --version 2>/dev/null || true")


def build_openjdk_lang():
    d = detect_distro()
    if d["family"] == "debian":
        return build_pkg(["default-jdk"], verify="java -version\njavac -version 2>/dev/null || true")
    if d["family"] == "arch":
        return build_pkg(["jdk-openjdk"], verify="java -version\njavac -version 2>/dev/null || true")
    if d["family"] == "fedora":
        return build_pkg(["java-21-openjdk-devel"], verify="java -version\njavac -version 2>/dev/null || true")
    if d["family"] == "suse":
        return (
            "set -e\n"
            + pkg_install(["java-21-openjdk-devel"]) + " || " + pkg_install(["java-17-openjdk-devel"]) + "\n"
            "echo '== Verificacao =='\njava -version\njavac -version 2>/dev/null || true\n"
        )
    return "echo 'Distribuicao nao suportada para OpenJDK'\n"


def build_nodejs_lang():
    d = detect_distro()
    if d["family"] == "debian":
        return (
            "set -e\n"
            "apt update && apt install -y curl ca-certificates\n"
            "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -\n"
            "apt install -y nodejs\n"
            "echo '== Versoes =='\nnode --version\nnpm --version\n"
        )
    if d["family"] == "fedora":
        return (
            "set -e\n"
            "dnf install -y curl\n"
            "curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -\n"
            "dnf install -y nodejs\n"
            "echo '== Versoes =='\nnode --version\nnpm --version\n"
        )
    if d["family"] == "arch":
        return build_pkg(["nodejs", "npm"], verify="node --version\nnpm --version")
    if d["family"] == "suse":
        return build_pkg(["nodejs", "npm"], verify="node --version\nnpm --version")
    return "echo 'Distribuicao nao suportada para Node.js'\n"


def build_cpp_lang():
    d = detect_distro()
    if d["family"] == "debian":
        pkgs = ["build-essential", "g++", "gcc", "make", "cmake", "pkg-config"]
    elif d["family"] == "fedora":
        pkgs = ["gcc-c++", "gcc", "make", "cmake", "pkgconf-pkg-config"]
    elif d["family"] == "arch":
        pkgs = ["base-devel", "cmake"]
    else:
        pkgs = ["gcc", "gcc-c++", "make", "cmake", "pkg-config"]
    return build_pkg(pkgs, verify="g++ --version | head -1\ncmake --version | head -1")


def build_rust_lang():
    return (
        "set -e\n"
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y\n"
        "echo '== Versao =='\n$HOME/.cargo/bin/rustc --version\n"
        "$HOME/.cargo/bin/cargo --version || true\n"
        "echo 'Rust pronto. Adicione ao PATH: export PATH=\"$HOME/.cargo/bin:$PATH\"'\n"
    )


def build_go_lang():
    d = detect_distro()
    if d["family"] == "debian":
        pkgs = ["golang-go"]
    elif d["family"] == "fedora":
        pkgs = ["golang"]
    elif d["family"] == "arch":
        pkgs = ["go"]
    else:
        pkgs = ["go"]
    return build_pkg(pkgs, verify="go version 2>/dev/null || true")


def build_ruby_lang():
    d = detect_distro()
    if d["family"] in ("debian", "fedora"):
        pkgs = ["ruby", "rubygems"]
    else:
        pkgs = ["ruby"]
    return build_pkg(pkgs, verify="ruby --version\ngem --version 2>/dev/null || true")


def build_php_lang():
    d = detect_distro()
    if d["family"] == "debian":
        return build_pkg(["php-cli", "php-xml", "php-mbstring"], verify="php --version | head -1")
    if d["family"] == "fedora":
        return build_pkg(["php-cli", "php-xml", "php-mbstring"], verify="php --version | head -1")
    if d["family"] == "arch":
        return build_pkg(["php", "php-xml", "php-mbstring"], verify="php --version | head -1")
    if d["family"] == "suse":
        return (
            "set -e\n"
            + pkg_install(["php84-cli"]) + " || " + pkg_install(["php83-cli"]) + " || "
            + pkg_install(["php-cli"]) + "\n"
            "echo '== Verificacao =='\nphp --version | head -1 || true\n"
        )
    return "echo 'Distribuicao nao suportada para PHP'\n"


# ==================================================================
# CATÁLOGO DE CATEGORIAS E ITENS
# ==================================================================
def _itens_sistema():
    return [
        {"id": "hw-detect", "name": "Detectar hardware", "desc": "GPU, rede, áudio, USB e drivers ativos",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_HARDWARE_DETECT},
        {"id": "sys-info", "name": "Informações do sistema", "desc": "Kernel, distro, uptime e carga",
         "kind": "info", "root": False, "danger": False,
         "script": "echo '== Sistema =='\nuname -a\ncat /etc/os-release 2>/dev/null | head -4\necho\nuptime\necho\nlscpu 2>/dev/null | grep -E 'Model name|CPU\\(s\\)|Architecture' || true\n"},
        {"id": "sys-failed", "name": "Serviços com falha", "desc": "Unidades systemd que precisam de atenção",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_FAILED_UNITS},
        {"id": "boot-analyze", "name": "Analisar tempo de boot", "desc": "Serviços que mais demoram a iniciar",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_BOOT},
    ]


def _itens_update():
    return [
        {"id": "update-full", "name": "Atualizar sistema completo", "desc": "Todos os pacotes da distro",
         "kind": "shell", "root": True, "danger": False, "script": lambda: build_full_update()},
        {"id": "update-refresh", "name": "Atualizar lista de pacotes", "desc": "Só o cache dos repositórios",
         "kind": "shell", "root": True, "danger": False, "script": lambda: build_repo_refresh()},
        {"id": "update-flatpak", "name": "Atualizar Flatpaks", "desc": "Apps do Flathub",
         "kind": "shell", "root": True, "danger": False, "script": build_flatpak_update},
        {"id": "update-snap", "name": "Atualizar Snaps", "desc": "Apps do snapd",
         "kind": "shell", "root": True, "danger": False, "script": build_snap_update},
        {"id": "update-cache", "name": "Limpar cache de pacotes", "desc": "Libera espaço do gerenciador",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_CLEAN},
    ]


def _itens_drivers():
    return [
        {"id": "nvidia", "name": "Driver NVIDIA", "desc": "Instala o driver proprietário NVIDIA (com CUDA)",
         "kind": "shell", "root": True, "danger": True, "script": build_nvidia},
        {"id": "nvidia-fix", "name": "Corrigir problema NVIDIA", "desc": "Tela preta / não inicia / conflito",
         "kind": "shell", "root": True, "danger": True, "script": build_nvidia_fix},
        {"id": "nouveau", "name": "Restaurar driver aberto (nouveau)", "desc": "Reversão segura da NVIDIA",
         "kind": "shell", "root": True, "danger": True, "script": build_nouveau_restore},
        {"id": "amd", "name": "Driver AMD/Radeon", "desc": "Mesa + Vulkan (código aberto)",
         "kind": "shell", "root": True, "danger": False, "script": build_amd},
        {"id": "intel", "name": "Driver Intel (i915)", "desc": "Mesa + VA-API para gráficos Intel",
         "kind": "shell", "root": True, "danger": False, "script": build_intel},
        {"id": "realtek-fw", "name": "Firmware Realtek", "desc": "Rede/Wi-Fi Realtek (oficial da distro)",
         "kind": "shell", "root": True, "danger": False, "script": build_realtek_firmware},
        {"id": "realtek-wifi", "name": "Wi-Fi Realtek rtl88xxau (DKMS)", "desc": "Driver rtl8188/8812au compilado",
         "kind": "shell", "root": True, "danger": True, "script": build_realtek_wifi},
        {"id": "acer", "name": "Hardware Acer (ACPI/fan)", "desc": "acpid + módulos acer-wmi/acerhdf",
         "kind": "shell", "root": True, "danger": False, "script": build_acer},
        {"id": "firmware", "name": "Atualizar todos os firmwares", "desc": "linux-firmware e amigos",
         "kind": "shell", "root": True, "danger": False, "script": build_firmware_update},
    ]


def _itens_repos():
    return [
        {"id": "repo-curl", "name": "curl", "desc": "Cliente HTTP para downloads",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: "set -e\n" + pkg_install(["curl"]) + "\necho 'curl pronto.'\n"},
        {"id": "repo-git", "name": "git", "desc": "Controle de versão",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: "set -e\n" + pkg_install(["git"]) + "\necho 'git pronto.'\n"},
        {"id": "repo-flatpak", "name": "flatpak + Flathub", "desc": "Pacotes universais + repositório Flathub",
         "kind": "shell", "root": True, "danger": False, "script": build_flatpak},
        {"id": "repo-snapd", "name": "snapd", "desc": "Pacotes Snap da Canonical",
         "kind": "shell", "root": True, "danger": False, "script": build_snapd},
        {"id": "repo-brew", "name": "Homebrew", "desc": "Gerador de pacotes macOS-style (sem root)",
         "kind": "shell", "root": False, "danger": False, "script": build_homebrew},
        {"id": "repo-nix", "name": "Nix", "desc": "Gerador de pacotes funcional (reprodutível)",
         "kind": "shell", "root": False, "danger": False, "script": build_nix},
        {"id": "repo-pip", "name": "pip (Python)", "desc": "Gerador de pacotes Python",
         "kind": "shell", "root": True, "danger": False, "script": build_pip},
        {"id": "repo-nonfree", "name": "Repositórios non-free (Debian/Ubuntu)", "desc": "Necessário p/ NVIDIA e firmwares",
         "kind": "shell", "root": True, "danger": False, "script": build_nonfree_repos},
        {"id": "repo-rpmfusion", "name": "RPM Fusion (Fedora)", "desc": "Repositórios livres/não-livres do Fedora",
         "kind": "shell", "root": True, "danger": False, "script": build_rpmfusion},
        {"id": "repo-multilib", "name": "Multilib (Arch/Manjaro)", "desc": "Bibliotecas 32-bit para games/Steam",
         "kind": "shell", "root": True, "danger": False, "script": build_multilib},
        {"id": "repo-packman", "name": "Packman (openSUSE)", "desc": "Codecs e mídia para openSUSE",
         "kind": "shell", "root": True, "danger": False, "script": build_packman},
        {"id": "repo-refresh", "name": "Atualizar cache dos repositórios", "desc": "Refresh da lista de pacotes",
         "kind": "shell", "root": True, "danger": False, "script": build_repo_refresh},
    ]


def _itens_kernels():
    return [
        {"id": "k-default", "name": "Kernel padrão (repositório)", "desc": "Kernel oficial da sua distro",
         "kind": "shell", "root": True, "danger": False, "script": build_kernel_default},
        {"id": "k-lts", "name": "Kernel LTS", "desc": "Série de suporte longo (estabilidade)",
         "kind": "shell", "root": True, "danger": False, "script": build_kernel_lts},
        {"id": "k-zen", "name": "Kernel Zen", "desc": "Modificado para desempenho (Arch)",
         "kind": "shell", "root": True, "danger": False, "script": build_kernel_zen},
        {"id": "k-xanmod", "name": "Kernel XanMod", "desc": "Modificado: scheduler xanmod, precacao, BBRS",
         "kind": "shell", "root": True, "danger": True, "script": build_kernel_xanmod},
        {"id": "k-liquorix", "name": "Kernel Liquorix", "desc": "Modificado: gaming e multimedia (Zen-based)",
         "kind": "shell", "root": True, "danger": True, "script": build_kernel_liquorix},
        {"id": "k-rt", "name": "Kernel RT (tempo real)", "desc": "Latência baixa: áudio/profissionais",
         "kind": "shell", "root": True, "danger": True, "script": build_kernel_rt},
        {"id": "k-download", "name": "Baixar mainline do kernel.org", "desc": "Download do tarball estável em ~/Downloads",
         "kind": "shell", "root": False, "danger": False, "script": build_kernel_download},
        {"id": "k-list", "name": "Listar kernels instalados", "desc": "Também mostra opções do GRUB",
         "kind": "info", "root": False, "danger": False, "script": build_kernel_list},
        {"id": "k-clean", "name": "Remover kernels antigos", "desc": "Limpa versões não usadas",
         "kind": "shell", "root": True, "danger": True, "script": build_kernel_remove_old},
    ]


def _itens_optimize():
    return [
        {"id": "opt-quick", "name": "Otimização rápida", "desc": "Swappiness + TRIM + log + cache",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_OPTIMIZE},
        {"id": "opt-zram", "name": "Habilitar ZRAM", "desc": "Memória comprimida (menos swap em disco)",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_ZRAM},
        {"id": "opt-swap", "name": "Swappiness = 10", "desc": "Prioriza RAM sobre swap",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_SWAPPINESS},
        {"id": "opt-trim", "name": "Habilitar TRIM (SSD)", "desc": "Manutenção semanal do SSD",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_TRIM},
        {"id": "opt-clean", "name": "Limpar logs e cache", "desc": "Libera espaço em disco",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_CLEAN},
        {"id": "opt-jobs", "name": "Compilação paralela (MAKEFLAGS)", "desc": "Usa todos os núcleos nas builds",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_MAKEFLAGS},
        {"id": "opt-boot", "name": "Analisar boot", "desc": "Ver serviços lentos e com falha",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_BOOT},
    ]


def _itens_dev():
    return [
        {"id": "dev-install", "name": "Instalar toolchains", "desc": "OpenJDK, g++, Python, Node, make, git",
         "kind": "shell", "root": True, "danger": False, "script": build_toolchain_install},
        {"id": "dev-openjdk", "name": "Ver toolchain OpenJDK", "desc": "java, javac e JAVA_HOME",
         "kind": "info", "root": False, "danger": False,
         "script": "echo '== OpenJDK =='\njava -version 2>&1 | head -2 || echo 'java nao instalado'\necho\njavac -version 2>&1 || echo 'javac ausente (so JRE)'\necho\n echo \"JAVA_HOME=${JAVA_HOME:-nao definido}\"\n"},
        {"id": "run-java", "name": "Executar Java (.java)", "desc": "Compila e roda com OpenJDK",
         "kind": "file", "root": False, "danger": False, "tool": "java", "filter": "*.java"},
        {"id": "run-cpp", "name": "Executar C++ (.cpp)", "desc": "Compila com g++ e executa",
         "kind": "file", "root": False, "danger": False, "tool": "cpp", "filter": "*.cpp *.cc *.cxx"},
        {"id": "run-python", "name": "Executar Python (.py)", "desc": "Roda com o Python do sistema",
         "kind": "file", "root": False, "danger": False, "tool": "python", "filter": "*.py"},
        {"id": "run-node", "name": "Executar Node.js (.js)", "desc": "Roda com o Node",
         "kind": "file", "root": False, "danger": False, "tool": "node", "filter": "*.js"},
        {"id": "run-shell", "name": "Executar script (.sh)", "desc": "Roda com bash",
         "kind": "file", "root": False, "danger": False, "tool": "shell", "filter": "*.sh"},
    ]


def _itens_health():
    return [
        {"id": "h-report", "name": "Relatório completo", "desc": "Disco, RAM, carga, falhas e processos",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_HEALTH_REPORT},
        {"id": "h-disk", "name": "Espaço em disco", "desc": "Uso de cada partição",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_DISK},
        {"id": "h-ram", "name": "Memória RAM e swap", "desc": "Uso de memória",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_RAM},
        {"id": "h-temp", "name": "Temperatura da CPU", "desc": "Sensores ou thermal zones",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_TEMP},
        {"id": "h-smart", "name": "Saúde do disco (SMART)", "desc": "Requer permissão de administrador",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_SMART},
        {"id": "h-failed", "name": "Falhas e erros do boot", "desc": "systemd + journal",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_FAILED_UNITS},
        {"id": "h-updates", "name": "Atualizações pendentes", "desc": "Pacotes esperando update",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_UPDATES_PENDING},
    ]


def _itens_net():
    return [
        {"id": "n-status", "name": "Status da rede", "desc": "Interfaces, rotas, DNS e ping",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_NET_STATUS},
        {"id": "n-wifi", "name": "Redes Wi-Fi próximas", "desc": "Lista redes (nmcli/iwctl)",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_WIFI},
        {"id": "n-firewall", "name": "Status do firewall", "desc": "ufw / firewalld / nftables",
         "kind": "info", "root": False, "danger": False, "script": SCRIPT_FIREWALL},
        {"id": "n-dns", "name": "Corrigir DNS", "desc": "Define 1.1.1.1 + 8.8.8.8 e limpa cache",
         "kind": "shell", "root": True, "danger": False, "script": lambda: SCRIPT_DNS_FIX},
    ]


def _itens_utils():
    return [
        {"id": "u-ls", "name": "Listar diretório (ls)", "desc": "Conteúdo de um diretório",
         "kind": "form", "root": False, "danger": False, "tool": "ls",
         "fields": [("caminho", ".")]},
        {"id": "u-cat", "name": "Mostrar arquivo (cat)", "desc": "Exibe o conteúdo de um arquivo",
         "kind": "file", "root": False, "danger": False, "tool": "cat", "filter": "*"},
        {"id": "u-grep", "name": "Buscar texto (grep)", "desc": "Procura um padrão nos arquivos",
         "kind": "form", "root": False, "danger": False, "tool": "grep",
         "fields": [("padrão", "TODO"), ("caminho", ".")]},
        {"id": "u-find", "name": "Encontrar arquivos (find)", "desc": "Busca por nome/padrão",
         "kind": "form", "root": False, "danger": False, "tool": "find",
         "argv_tmpl": ["find", "{0}", "-name", "{1}"],
         "fields": [("caminho", "."), ("padrão", "*.py")]},
        {"id": "u-pwd", "name": "Diretório atual (pwd)", "desc": "Mostra onde você está",
         "kind": "info", "root": False, "danger": False, "script": "pwd\n"},
        {"id": "u-mkdir", "name": "Criar diretório (mkdir)", "desc": "Cria uma pasta",
         "kind": "form", "root": False, "danger": False, "tool": "mkdir",
         "fields": [("nome", "nova-pasta")]},
        {"id": "u-cp", "name": "Copiar (cp)", "desc": "Copia arquivo/pasta",
         "kind": "form", "root": False, "danger": False, "tool": "cp",
         "fields": [("origem", "arquivo.txt"), ("destino", "cópia.txt")]},
        {"id": "u-mv", "name": "Mover/renomear (mv)", "desc": "Move ou renomeia",
         "kind": "form", "root": False, "danger": False, "tool": "mv",
         "fields": [("origem", "antigo.txt"), ("destino", "novo.txt")]},
        {"id": "u-chmod", "name": "Permissões (chmod)", "desc": "Muda modo de acesso (ex.: 755)",
         "kind": "form", "root": False, "danger": True, "tool": "chmod",
         "fields": [("modo", "755"), ("caminho", "script.sh")]},
        {"id": "u-rm", "name": "Remover (rm)", "desc": "Apaga arquivo/pasta",
         "kind": "form", "root": False, "danger": True, "tool": "rm",
         "fields": [("caminho", "arquivo.txt")]},
        {"id": "u-echo", "name": "Exibir texto (echo)", "desc": "Imprime uma linha",
         "kind": "form", "root": False, "danger": False, "tool": "echo",
         "fields": [("texto", "Olá do lunuz!")]},
    ]


def _itens_ide():
    return [
        # --- IDEs e editores ---
        {"id": "ide-vscode", "name": "Visual Studio Code", "desc": "IDE da Microsoft (Flatpak/repo oficial)",
         "kind": "shell", "root": True, "danger": False, "script": build_vscode},
        {"id": "ide-vscodium", "name": "VSCodium", "desc": "VS Code sem telemetria (Flathub)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_flatpak_app("com.vscodium.codium", "VSCodium")},
        {"id": "ide-sublime", "name": "Sublime Text", "desc": "Editor leve (repositório oficial)",
         "kind": "shell", "root": True, "danger": False, "script": build_sublime},
        {"id": "ide-intellij", "name": "IntelliJ IDEA Community", "desc": "IDE para Java/Kotlin (Flathub)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_flatpak_app("com.jetbrains.IntelliJ-IDEA-IC", "IntelliJ IDEA")},
        {"id": "ide-pycharm", "name": "PyCharm Community", "desc": "IDE para Python (Flathub)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_flatpak_app("com.jetbrains.PyCharm-Community", "PyCharm")},
        {"id": "ide-eclipse", "name": "Eclipse", "desc": "IDE clássica multi-linguagem (Flathub)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_flatpak_app("org.eclipse.EclipseIDE", "Eclipse")},
        {"id": "ide-zed", "name": "Zed", "desc": "Editor rápido da Zed Industries (usuário)",
         "kind": "shell", "root": False, "danger": False, "script": build_zed},
        # --- Editores de texto ---
        {"id": "ed-neovim", "name": "Neovim", "desc": "Editor modal moderno (terminal)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_pkg(["neovim"], verify="nvim --version | head -1")},
        {"id": "ed-vim", "name": "Vim", "desc": "O clássico editor de terminal",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_pkg(["vim"], verify="vim --version | head -1")},
        {"id": "ed-emacs", "name": "Emacs", "desc": "Editor/extensor de propósito geral",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_pkg(["emacs"], verify="emacs --version | head -1")},
        {"id": "ed-kate", "name": "Kate", "desc": "Editor avançado do KDE",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_pkg(["kate"], verify="kate --version 2>/dev/null | head -1 || true")},
        {"id": "ed-gnome", "name": "Editor de textos GNOME", "desc": "gedit / GNOME Text Editor",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: (
             "set -e\n" + pkg_install(["gnome-text-editor"]) + " || " +
             pkg_install(["gedit"]) + "\necho 'Editor de textos instalado.'\n")},
        {"id": "ed-nano", "name": "Nano", "desc": "Editor de terminal simples",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_pkg(["nano"], verify="nano --version | head -1")},
        # --- Agentes de IA ---
        {"id": "ai-ollama", "name": "Ollama", "desc": "LLMs locais (Llama, Mistral...)",
         "kind": "shell", "root": False, "danger": False, "script": build_ollama},
        {"id": "ai-aider", "name": "Aider", "desc": "Agente de IA que edita seu código no terminal",
         "kind": "shell", "root": False, "danger": False, "script": build_aider},
        {"id": "ai-claude", "name": "Claude Code", "desc": "Agente de IA da Anthropic (npm)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_npm_agent("@anthropic-ai/claude-code", "Claude Code", "claude")},
        {"id": "ai-gemini", "name": "Gemini CLI", "desc": "Agente de IA do Google (npm)",
         "kind": "shell", "root": True, "danger": False,
         "script": lambda: build_npm_agent("@google/gemini-cli", "Gemini CLI", "gemini")},
        # --- Ferramentas ---
        {"id": "tool-essential", "name": "Ferramentas essenciais", "desc": "git, gh, htop, btop, jq, ripgrep, fzf, tmux",
         "kind": "shell", "root": True, "danger": False, "script": build_essential_tools},
        {"id": "tool-docker", "name": "Docker Engine", "desc": "Containers (script oficial)",
         "kind": "shell", "root": True, "danger": False, "script": build_docker},
    ]


def _itens_lang():
    return [
        {"id": "lang-python", "name": "Python 3 + pip + venv", "desc": "Linguagem e ecossistema oficiais",
         "kind": "shell", "root": True, "danger": False, "script": build_python_lang},
        {"id": "lang-java", "name": "OpenJDK (Java)", "desc": "JDK completo para Java",
         "kind": "shell", "root": True, "danger": False, "script": build_openjdk_lang},
        {"id": "lang-node", "name": "Node.js LTS + npm", "desc": "Runtime JavaScript (NodeSource 22)",
         "kind": "shell", "root": True, "danger": False, "script": build_nodejs_lang},
        {"id": "lang-cpp", "name": "C/C++ (g++, make, cmake)", "desc": "Compilador e ferramentas nativas",
         "kind": "shell", "root": True, "danger": False, "script": build_cpp_lang},
        {"id": "lang-rust", "name": "Rust + Cargo", "desc": "rustup oficial (usuário)",
         "kind": "shell", "root": False, "danger": False, "script": build_rust_lang},
        {"id": "lang-go", "name": "Go", "desc": "Linguagem da Google",
         "kind": "shell", "root": True, "danger": False, "script": build_go_lang},
        {"id": "lang-ruby", "name": "Ruby + Gems", "desc": "Linguagem e gerenciador de pacotes",
         "kind": "shell", "root": True, "danger": False, "script": build_ruby_lang},
        {"id": "lang-php", "name": "PHP", "desc": "CLI + extensões comuns (web)",
         "kind": "shell", "root": True, "danger": False, "script": build_php_lang},
    ]


CATEGORIES = [
    {"id": "system", "name": "Sistema", "icon": "preferences-system-symbolic",
     "color": "#4f7fd9", "items": _itens_sistema()},
    {"id": "update", "name": "Atualizar Sistema", "icon": "view-refresh-symbolic",
     "color": "#3d9bd9", "items": _itens_update()},
    {"id": "drivers", "name": "Drivers e Hardware", "icon": "video-display-symbolic",
     "color": "#d9534f", "items": _itens_drivers()},
    {"id": "repos", "name": "Repositórios Adicionais", "icon": "folder-download-symbolic",
     "color": "#d99a3d", "items": _itens_repos()},
    {"id": "kernels", "name": "Kernels Linux", "icon": "applications-system-symbolic",
     "color": "#5a6270", "items": _itens_kernels()},
    {"id": "optimize", "name": "Otimização do Sistema", "icon": "media-playback-start-symbolic",
     "color": "#c9a227", "items": _itens_optimize()},
    {"id": "dev", "name": "Desenvolvedores", "icon": "application-x-executable-symbolic",
     "color": "#8a5ad9", "items": _itens_dev()},
    {"id": "ide", "name": "IDEs, Editores e IA", "icon": "text-editor-symbolic",
     "color": "#b85cd9", "items": _itens_ide()},
    {"id": "lang", "name": "Linguagens de Programação", "icon": "applications-science-symbolic",
     "color": "#d97b2e", "items": _itens_lang()},
    {"id": "health", "name": "Saúde e Bem-estar", "icon": "battery-symbolic",
     "color": "#d93d6e", "items": _itens_health()},
    {"id": "net", "name": "Rede e Internet", "icon": "network-server-symbolic",
     "color": "#2e9dd9", "items": _itens_net()},
    {"id": "utils", "name": "Utilidades", "icon": "text-x-generic-symbolic",
     "color": "#3db96e", "items": _itens_utils()},
    {"id": "terminal", "name": "Terminal", "icon": "utilities-terminal-symbolic",
     "color": "#26b0a8", "items": []},
]


# ==================================================================
# Ícone específico de cada item (estilo LinuxToys: um ícone por coisa).
# Itens sem entrada aqui usam o ícone da própria categoria.
# ==================================================================
ITEM_ICONS = {
    # --- Sistema ---
    "hw-detect": "computer-symbolic",
    "sys-info": "dialog-information-symbolic",
    "sys-failed": "dialog-warning-symbolic",
    "boot-analyze": "document-properties-symbolic",
    # --- Atualizar Sistema ---
    "update-full": "media-playlist-repeat-symbolic",
    "update-refresh": "view-refresh-symbolic",
    "update-flatpak": "package-x-generic-symbolic",
    "update-snap": "system-software-install-symbolic",
    "update-cache": "edit-clear-symbolic",
    # --- Drivers e Hardware ---
    "nvidia": "video-display-symbolic",
    "nvidia-fix": "applications-engineering-symbolic",
    "nouveau": "view-refresh-symbolic",
    "amd": "media-flash-symbolic",
    "intel": "computer-symbolic",
    "realtek-fw": "package-x-generic-symbolic",
    "realtek-wifi": "network-wireless-symbolic",
    "acer": "battery-good-symbolic",
    "firmware": "software-update-available-symbolic",
    # --- Repositórios ---
    "repo-curl": "network-transmit-receive-symbolic",
    "repo-git": "media-playlist-repeat-symbolic",
    "repo-flatpak": "package-x-generic-symbolic",
    "repo-snapd": "system-software-install-symbolic",
    "repo-brew": "folder-download-symbolic",
    "repo-nix": "applications-science-symbolic",
    "repo-pip": "application-x-executable-symbolic",
    "repo-nonfree": "security-high-symbolic",
    "repo-rpmfusion": "package-x-generic-symbolic",
    "repo-multilib": "view-grid-symbolic",
    "repo-packman": "media-playlist-repeat-symbolic",
    "repo-refresh": "view-refresh-symbolic",
    # --- Kernels ---
    "k-default": "applications-system-symbolic",
    "k-lts": "battery-full-symbolic",
    "k-zen": "face-smile-symbolic",
    "k-xanmod": "media-flash-symbolic",
    "k-liquorix": "applications-games-symbolic",
    "k-rt": "alarm-symbolic",
    "k-download": "folder-download-symbolic",
    "k-list": "view-list-symbolic",
    "k-clean": "list-remove-symbolic",
    # --- Otimização ---
    "opt-quick": "media-playback-start-symbolic",
    "opt-zram": "media-flash-symbolic",
    "opt-swap": "view-refresh-symbolic",
    "opt-trim": "drive-harddisk-symbolic",
    "opt-clean": "edit-delete-symbolic",
    "opt-jobs": "applications-engineering-symbolic",
    "opt-boot": "alarm-symbolic",
    # --- Desenvolvedores ---
    "dev-install": "applications-engineering-symbolic",
    "dev-openjdk": "applications-science-symbolic",
    "run-java": "media-playback-start-symbolic",
    "run-cpp": "system-run-symbolic",
    "run-python": "text-x-generic-symbolic",
    "run-node": "network-transmit-receive-symbolic",
    "run-shell": "utilities-terminal-symbolic",
    # --- IDEs, Editores e IA ---
    "ide-vscode": "text-editor-symbolic",
    "ide-vscodium": "text-x-generic-symbolic",
    "ide-sublime": "format-text-bold-symbolic",
    "ide-intellij": "applications-science-symbolic",
    "ide-pycharm": "insert-text-symbolic",
    "ide-eclipse": "applications-engineering-symbolic",
    "ide-zed": "text-editor-symbolic",
    "ed-neovim": "utilities-terminal-symbolic",
    "ed-vim": "system-search-symbolic",
    "ed-emacs": "insert-text-symbolic",
    "ed-kate": "document-properties-symbolic",
    "ed-gnome": "text-x-generic-symbolic",
    "ed-nano": "utilities-terminal-symbolic",
    "ai-ollama": "computer-symbolic",
    "ai-aider": "avatar-default-symbolic",
    "ai-claude": "face-smile-symbolic",
    "ai-gemini": "applications-science-symbolic",
    "tool-essential": "applications-engineering-symbolic",
    "tool-docker": "package-x-generic-symbolic",
    # --- Linguagens de Programação ---
    "lang-python": "text-x-generic-symbolic",
    "lang-java": "applications-science-symbolic",
    "lang-node": "system-run-symbolic",
    "lang-cpp": "applications-engineering-symbolic",
    "lang-rust": "security-high-symbolic",
    "lang-go": "media-skip-forward-symbolic",
    "lang-ruby": "media-flash-symbolic",
    "lang-php": "web-browser-symbolic",
    # --- Saúde ---
    "h-report": "dialog-information-symbolic",
    "h-disk": "drive-harddisk-symbolic",
    "h-ram": "media-flash-symbolic",
    "h-temp": "weather-storm-symbolic",
    "h-smart": "security-high-symbolic",
    "h-failed": "dialog-warning-symbolic",
    "h-updates": "software-update-available-symbolic",
    # --- Rede ---
    "n-status": "network-transmit-receive-symbolic",
    "n-wifi": "network-wireless-symbolic",
    "n-firewall": "security-high-symbolic",
    "n-dns": "system-search-symbolic",
    # --- Utilidades ---
    "u-ls": "view-list-symbolic",
    "u-cat": "document-open-symbolic",
    "u-grep": "system-search-symbolic",
    "u-find": "document-open-recent-symbolic",
    "u-pwd": "folder-open-symbolic",
    "u-mkdir": "list-add-symbolic",
    "u-cp": "edit-copy-symbolic",
    "u-mv": "edit-paste-symbolic",
    "u-chmod": "security-high-symbolic",
    "u-rm": "edit-delete-symbolic",
    "u-echo": "insert-text-symbolic",
}


def item_icon(item):
    """Ícone do item (estilo LinuxToys); fallback: ícone da categoria."""
    return ITEM_ICONS.get(item.get("id", ""), "")


# ==================================================================
# Disponibilidade por distro (família).
# Itens SEM entrada em AVAILABILITY executam em todas as famílias.
# ==================================================================
AVAILABILITY = {
    "repo-nonfree": ("debian",),
    "repo-rpmfusion": ("fedora",),
    "repo-multilib": ("arch",),
    "repo-packman": ("suse",),
    "k-zen": ("arch",),
    "k-rt": ("debian", "fedora", "arch"),
    "k-liquorix": ("debian",),
    "k-xanmod": ("debian", "arch"),
}

FAMILY_NAMES = {
    "debian": "Debian/Ubuntu",
    "fedora": "Fedora/RHEL",
    "arch": "Arch/Manjaro",
    "suse": "openSUSE",
    "unknown": "não identificada",
}

PKG_MGRS = {
    "debian": "apt (dpkg)",
    "fedora": "dnf (rpm)",
    "arch": "pacman",
    "suse": "zypper (rpm)",
    "unknown": "-",
}


def available_families(item):
    """Famílias onde a ação executa de verdade; vazio = todas."""
    return AVAILABILITY.get(item.get("id", ""), ())


def item_available(item, family=None):
    """True se a ação está disponível na família (padrão: a detectada)."""
    fam = family or detect_distro()["family"]
    allowed = available_families(item)
    return not allowed or fam in allowed


def distro_report(list_available=False):
    """Relatório textual do identificador de distro + ações disponíveis."""
    d = detect_distro()
    fam = d["family"]
    items = [it for cat in CATEGORIES for it in cat["items"]]
    avail = [it for it in items if item_available(it, fam)]
    blocked = [it for it in items if not item_available(it, fam)]
    nome = d["name"] + (f" {d['version']}" if d["version"] else "")
    linhas = [
        "lunuz tools - identificador de distro",
        "=====================================",
        f"Sistema:  {nome}",
        f"ID:       {d['id']}",
        f"Familia:  {FAMILY_NAMES.get(fam, fam)} ({fam})",
        f"Pacotes:  {PKG_MGRS.get(fam, '-')}",
        f"Acoes:    {len(items)} total - {len(avail)} disponiveis aqui, "
        f"{len(blocked)} indisponiveis",
    ]
    if blocked:
        linhas.append("")
        linhas.append("Indisponiveis nesta distro:")
        for it in blocked:
            fams = ", ".join(FAMILY_NAMES.get(f, f) for f in available_families(it))
            linhas.append(f"  - {it['name']}  (so em: {fams})")
    if list_available:
        linhas.append("")
        linhas.append(f"Disponiveis aqui ({len(avail)}):")
        for it in avail:
            linhas.append(f"  - [{it['id']}] {it['name']}")
    elif blocked:
        linhas.append("")
        linhas.append("Use `lunuz distro --list` para listar as acoes disponiveis.")
    return "\n".join(linhas)


def all_items():
    """Lista plana de (categoria, item) para busca."""
    out = []
    for cat in CATEGORIES:
        for item in cat["items"]:
            out.append((cat, item))
    return out
