# 🌙 lunuz tools (Linuz-Tools)

<div align="center">

**Versão 1.0.5** 🏷️

Coleção de utilitários Linux com interface gráfica inspirada na
**LinuxToys** (grade de seções com ícones, busca e terminal embutido).

🖥️ **Debian/Ubuntu** • 🎀 **Arch/Manjaro** • 🎩 **Fedora/RHEL** • 🦎 **openSUSE** • 🎮 **SteamOS**

> 🇺🇸 English version: [README.md](README.md)

</div>

---

## ✨ O que ele faz

- 🪟 **Windows no Linux** — Wine, Steam, Lutris, Bottles, Proton-GE, WinBoat e mais
- 🧰 **Drivers e Kernels** — NVIDIA, AMD, Intel, Realtek, XanMod, Liquorix, RT...
- 📦 **Repositórios automáticos** — o app adiciona sozinho o repositório que falta
- 🌍 **11 idiomas** — detecta o idioma do sistema e troca na hora, sem reiniciar
- 🖲️ **Terminal embutido** — acompanhe cada instalação em tempo real

## 🗺️ Seções (**14 seções / 112 recursos**)

| Seção | Conteúdo |
|-------|----------|
| 🖥️ Sistema | Detectar hardware, informações, serviços com falha, boot |
| 🔄 Atualizar Sistema | Update completo, Flatpak, Snap, cache de pacotes |
| 🧰 Drivers e Hardware | **NVIDIA** (instalar/corrigir/nouveau), **AMD**, Intel, **Realtek** (firmware + Wi-Fi DKMS), **Acer** (ACPI/fan), firmware geral |
| 📡 Repositórios Adicionais | **curl, git, flatpak, snapd, Homebrew, Nix, pip** + non-free (Debian), RPM Fusion (Fedora), multilib (Arch), Packman (openSUSE) |
| 🧠 Kernels Linux | Padrão, LTS, **Zen, XanMod, Liquorix, RT** (modificados), **download do mainline (kernel.org)**, listar, remover antigos |
| 🚀 Otimização do Sistema | Otimização rápida, ZRAM, swappiness, TRIM, limpeza, MAKEFLAGS, boot |
| 👨‍💻 Desenvolvedores | Toolchains (OpenJDK, g++, Python, Node) e execução de arquivos |
| ✏️ IDEs, Editores e IA | **VS Code, VSCodium, Sublime Text, IntelliJ IDEA, PyCharm, Eclipse, Zed**; **Neovim, Vim, Emacs, Kate, GNOME, Nano**; IA **Ollama, Aider, Claude Code, Gemini CLI**; ferramentas e **Docker** |
| 🪟 **Windows no Linux** | **Wine** (repo WineHQ automático), **Winetricks**, **Bottles**, **Lutris**, **ProtonUp-Qt** (Proton-GE), **Heroic**, **Steam**, **PlayOnLinux**, **WinBoat** (Windows 11 em container) e **GameMode + MangoHud** |
| 🔤 Linguagens de Programação | **Python 3 + pip, OpenJDK, Node.js LTS, C/C++, Rust, Go, Ruby, PHP** |
| 🩺 Saúde e Bem-estar | Relatório, disco, RAM, temperatura, **SMART**, falhas, updates |
| 🌐 Rede e Internet | Status, Wi-Fi, firewall, **corrigir DNS** |
| 🧩 Utilidades | Todos os comandos CLI (ls, grep, find, chmod...) com diálogos |
| 💻 **Terminal** | Aba dedicada para acompanhar o progresso (spinner, status, contador de etapas) |

## 🪟 Seção «Windows no Linux»

Tudo o que você precisa para rodar programas e jogos do Windows, **com os
repositórios oficiais habilitados automaticamente** (WineHQ, multilib,
RPM Fusion, Packman...):

| Item | Para que serve |
|------|----------------|
| 🍷 Wine | Rodar programas `.exe` (repositório WineHQ adicionado sozinho) |
| 🧪 Winetricks | DLLs e componentes do Windows para o Wine |
| 🍾 Bottles | Apps/jogos em "garrafas" isoladas (Flatpak) |
| 🎯 Lutris | Central de jogos com instaladores da comunidade |
| ⏫ ProtonUp-Qt | Instala/atualiza o **Proton-GE** do Steam |
| 🦸 Heroic | Epic, GOG e Amazon Games no Linux |
| 🎮 Steam | Loja da Valve (habilita multilib/RPM Fusion/Packman sozinho) |
| 🐧 PlayOnLinux | Assistente clássico via Wine |
| 🚢 **WinBoat** | **Windows 11 real** em container Docker, integrado ao desktop |
| ⚡ GameMode + MangoHud | Boost de desempenho e overlay de FPS |

## 📦 Repositórios automáticos (o destaque da v1.0.5)

💡 **Nunca mais veja "pacote não encontrado" por falta de repositório.**
Quando você pede um driver/kernel/aplicativo que precisa de um repositório
que não existe na sua distro, o lunuz **adiciona o repositório sozinho**
antes de instalar:

| Ação | Repositório adicionado automaticamente |
|------|----------------------------------------|
| 🧰 Driver NVIDIA (Debian) | `contrib` + `non-free` + `non-free-firmware` |
| 🧰 Driver NVIDIA (Fedora) | **RPM Fusion** (free + nonfree) |
| 🧰 Driver NVIDIA (openSUSE) | Repo oficial da NVIDIA |
| 🧰 AMD/Intel (Arch) | **multilib** (pacotes `lib32-*`) |
| 🧠 Kernel XanMod (Debian) | repo + chave do **XanMod** |
| 🧠 Kernel XanMod (Arch) | **chaotic-aur** (keyring + mirrorlist) |
| 🧠 Kernel Liquorix (Debian) | repo + chave do **Liquorix** |
| 🎮 Steam (Fedora/Arch/openSUSE) | RPM Fusion / multilib / Packman |
| 🍷 Wine (Debian) | **WineHQ** (com fallback para o pacote da distro) |
| 🚢 WinBoat | Docker + download da última release do GitHub |

## 🌍 11 idiomas, detecção automática

A interface detecta o idioma do sistema (`LANG`/`LC_ALL`) e aplica a
tradução correspondente — **inglês (EUA) é o padrão** quando o idioma não
é suportado. Para trocar manualmente:

> ⚙️ **Engrenagem no cabeçalho → Configurações → Idioma**

| 🏳️ Idiomas |
|-------------|
| 🇺🇸 English (US) 🇬🇧 English (UK) 🇦🇺 English (Australia) 🇧🇷 Português (Brasil) 🇵🇹 Português (Portugal) 🇷🇺 Русский 🇯🇵 日本語 🇨🇳 中文（简体） 🇩🇪 Deutsch 🇰🇷 한국어 🇻🇳 Tiếng Việt |

- A troca é **instantânea** (sem reiniciar o app) e fica salva em
  `~/.config/lunuz/settings.json`
- Traduz **tudo**: seções, itens, busca, diálogos, fila de execução e o
  comando `lunuz distro`

## 🖥️ Interface (estilo LinuxToys)

- ✨ **Ícone distinto para cada um dos 112 recursos**, com ícones de marca
  (NVIDIA, AMD, Docker, VS Code, Python...) e quadrados coloridos gerados
  para o resto
- 🆔 **Chip da distro** na home: logo, família e quantas ações estão
  disponíveis; ações de outras distros ficam esmaecidas com selo "só em..."
- 🔍 **Busca** instantânea que filtra os 112 recursos (no seu idioma)
- 🔲 **Grade/lista** alternáveis no cabeçalho
- ✅ **Seleção múltipla**: marque vários itens e execute **em sequência
  com uma única confirmação**
- 🚦 **Fila de execução**: uma ação por vez — a saída nunca se mistura
- ⌨️ `Esc` limpa a busca/vai para home • `Ctrl+F` foca a busca • botão
  **voltar** sempre disponível
- 🔐 Ações administrativas usam **pkexec**; ações perigosas pedem
  **confirmação prévia**

## 🚀 Como executar (sem terminal)

1. 🖱️ **Clique duplo** no `linuz_tools-x86_64.AppImage` — a GUI abre sozinha
2. 📋 Procure **"lunuz tools"** no menu de aplicativos
3. 🖼️ Ícone `lunuz-tools.desktop` na área de trabalho

### Opções avançadas (terminal)

```bash
lunuz gui                      # interface gráfica
./linuz_tools-x86_64.AppImage --help                        # CLI direto
./linuz_tools-x86_64.AppImage --appimage-extract-and-run    # SEM FUSE
```

> 💡 Se o AppImage não montar (FUSE ausente), use
> `--appimage-extract-and-run`. Sem GTK/VTE, um popup (zenity) explica o
> que instalar.

## ⌨️ Comandos CLI (22)

| Categoria | Comandos |
|-----------|----------|
| 📁 Arquivos | `ls` `pwd` `cd` `cat` `echo` `mkdir` `rm` `cp` `mv` |
| 🔎 Busca | `grep` `find` |
| 🔐 Permissões | `chmod` (numérico **e simbólico**: `+x`, `u+x`, `go-w`) `chown` |
| 🗣️ Linguagens | `java` `cpp` `python` `node` `shell` |
| 🛠️ Sistema | `openjdk` `distro` `gui` `--version` |

```bash
lunuz ls -la /tmp
lunuz cpp main.cpp              # compila e roda C++
lunuz chmod +x script.sh        # modo simbólico agora funciona!
lunuz distro                    # distro + ações disponíveis aqui
lunuz distro --list             # lista todas as ações disponíveis
lunuz gui                       # interface gráfica
```

## 📥 Instalação

Os pacotes ficam em `dist/` (gere você mesmo com `scripts/make_dist.sh`):

| Formato | Arquivo | Instalação |
|---------|---------|------------|
| 🧊 Debian/Ubuntu | `lunuz-tools_1.0.5_all.deb` | `sudo apt install ./lunuz-tools_1.0.5_all.deb` |
| 🎩 Fedora/RHEL | `lunuz-tools-1.0.5-1.noarch.rpm` | `sudo dnf install ./lunuz-tools-1.0.5-1.noarch.rpm` |
| 🎀 Arch/Manjaro | `lunuz-tools-1.0.5-1-any.pkg.tar.zst` | `sudo pacman -U ...pkg.tar.zst` |
| 📦 Tarballs/Zip | `.tar.gz` `.tar.xz` `.zip`... | extraia e rode `python3 -m lunuz gui` |
| 🐞 Flatpak | `org.davi.lunuz-tools.json` | `flatpak-builder build org.davi.lunuz-tools.json` |
| 🦑 Snap | `snapcraft.yaml` | `snapcraft` |

### Dependências da GUI

| Distro | Pacotes |
|--------|---------|
| 🧊 Debian/Ubuntu | `sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91` |
| 🎩 Fedora/RHEL | `sudo dnf install python3 python3-gobject gtk3 vte291` |
| 🎀 Arch/Manjaro | `sudo pacman -S python python-gobject gtk3 vte3` |
| 🦎 openSUSE | `sudo zypper in python3 python3-gobject gtk3 vte-2_91` |
| 🎮 SteamOS | AppImage com `--appimage-extract-and-run` |

## ✅ Testes

Três suítes automatizadas cobrem a interface inteira (navegação, busca,
voltar, alternância de visão, os 112 itens, fila de execução com terminal
real, seleção múltipla e todos os diálogos):

```bash
python3 tests/test_gui_programatic.py   # 🎛️ tiles/busca/voltar + 112 itens
python3 tests/test_terminal_queue.py    # 🚦 fila real: serialização + progresso
python3 tests/test_gui_dialogs.py       # 💬 formulários/arquivos/confirmações reais
```

## 🗂️ Estrutura

```
lunuz_tools/
├── lunuz/                  # pacote Python
│   ├── cli.py              # CLI (22 comandos)
│   ├── gui.py              # interface GTK3 + VTE
│   ├── actions.py          # catálogo de ações (scripts por distro)
│   ├── tools.py            # utilitários de linha de comando
│   ├── i18n.py             # 🌍 detecção de idioma + troca
│   ├── ui_translations.py  # textos da interface (11 idiomas)
│   ├── item_translations.py# nomes/descrições dos itens (8 idiomas)
│   └── icons/              # ícones por seção/item/distro
├── tests/                  # 3 suítes de teste da GUI
├── scripts/                # make_dist.sh + gerador de ícones
├── dist/                   # pacotes gerados
└── linuz_tools-x86_64.AppImage
```

## 🤝 Contribuindo

1. 🍴 Faça um fork
2. 🌱 Crie sua branch (`git checkout -b minha-feature`)
3. ✅ Rode os testes
4. 📤 Abra um Pull Request

---

<div align="center">

Feito com 💙 para o Linux • [Reportar Bug](https://github.com/DAVIB3BR/Linuz-Tools/issues) • [Repositório](https://github.com/DAVIB3BR/Linuz-Tools)

</div>
