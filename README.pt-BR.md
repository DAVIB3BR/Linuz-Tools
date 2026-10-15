# lunuz tools

Coleção de utilitários de linha de comando para Linux com interface gráfica
inspirada na **LinuxToys** (grade de seções com ícones, busca e terminal
embutido). Funciona em Debian/Ubuntu, Arch/Manjaro, Fedora/RHEL, openSUSE,
SteamOS e derivados.

> Versão em inglês disponível em [README.md](README.md).

## Interface gráfica (estilo LinuxToys)

Clique duplo no AppImage, no ícone da Área de Trabalho ou "lunuz tools"
no menu de aplicativos. Seções disponíveis (**13 seções / 102 recursos**):

| Seção | Conteúdo |
|-------|----------|
| Sistema | Detectar hardware, informações, serviços com falha, boot |
| Atualizar Sistema | Update completo, Flatpak, Snap, cache de pacotes |
| Drivers e Hardware | **NVIDIA** (instalar/corrigir/nouveau), **AMD**, Intel, **Realtek** (firmware + Wi-Fi DKMS), **Acer** (ACPI/fan), firmware geral |
| Repositórios Adicionais | **curl, git, flatpak, snapd, Homebrew, Nix, pip** + non-free (Debian), RPM Fusion (Fedora), multilib (Arch), Packman (openSUSE) |
| Kernels Linux | Padrão, LTS, **Zen, XanMod, Liquorix, RT** (modificados), **download do mainline (kernel.org)**, listar, remover antigos |
| Otimização do Sistema | Otimização rápida, ZRAM, swappiness, TRIM, limpeza, MAKEFLAGS, boot |
| Desenvolvedores | Instalar toolchains (OpenJDK, g++, Python, Node) e executar arquivos |
| IDEs, Editores e IA | **VS Code, VSCodium, Sublime Text, IntelliJ IDEA, PyCharm, Eclipse, Zed**; **Neovim, Vim, Emacs, Kate, Editor de textos GNOME, Nano**; agentes de IA **Ollama, Aider, Claude Code, Gemini CLI**; ferramentas essenciais e **Docker** |
| Linguagens de Programação | **Python 3 + pip, OpenJDK (Java), Node.js LTS, C/C++, Rust, Go, Ruby, PHP** |
| Saúde e Bem-estar | Relatório, disco, RAM, temperatura, **SMART**, falhas, updates |
| Rede e Internet | Status, Wi-Fi, firewall, **corrigir DNS** |
| Utilidades | Todos os comandos CLI (ls, grep, find, chmod...) com diálogos |
| **Terminal** | **Aba dedicada para acompanhar o progresso da instalação** (spinner, status, contador de etapas) |

Recursos da interface:

- **Ícone distinto para cada um dos 102 recursos** (estilo LinuxToys),
  com **ícones de marca onde importa** (NVIDIA, AMD, Intel, Docker,
  VS Code, Python, Java, Rust...) e ícones coloridos gerados para o
  resto, além do ícone da seção no cabeçalho e nos botões de ação
- **Identificador de distro**: um chip na home mostra a distro
  detectada (logo, família, versão) e quantas das 102 ações estão
  disponíveis aqui; ações de outras distros aparecem esmaecidas com
  selo "só em ..." e o clique explica onde elas funcionam —
  `lunuz distro` faz o mesmo pelo terminal (use `--list`)
- **Busca** no header filtra os 102 recursos
- **Modos grade/lista** no header
- **Seleção múltipla**: ative "Seleção múltipla", marque vários itens
  shell e execute **todos em sequência com uma única confirmação**
- **Fila de execução**: as ações rodam uma de cada vez — a saída nunca
  se mistura; o progresso aparece na **aba Terminal** e na linha de status
- **Botão voltar** retorna categoria → home (e busca → página de origem);
  `Esc` limpa a busca / vai para home, `Ctrl+F` foca a busca
- **Terminal VTE** embutido mostra a saída de cada ação
- Ações administrativas usam **pkexec** (pede autenticação) e as
  perigosas (drivers/kernels) pedem **confirmação prévia**
- Scripts são adaptados automaticamente à sua distro detectada

## Como executar (como um APP, sem terminal)

### 1. Clique duplo no AppImage
Basta clicar duas vezes em `lunuz-x86_64.AppImage` — **abre a interface
gráfica automaticamente** (como um programa normal).

### 2. Menu de aplicativos (KDE/GNOME)
Procure **"lunuz tools"** no menu de aplicativos — já está registrado.

### 3. Ícone na Área de Trabalho
`lunuz-tools.desktop` na Área de Trabalho (marcado como confiável,
clique duplo abre o app).

### Opções avançadas (terminal)
```bash
lunuz gui            # interface gráfica
./lunuz-x86_64.AppImage --help          # CLI direto
./lunuz-x86_64.AppImage --appimage-extract-and-run --help   # SEM FUSE
```

> Se o AppImage não montar (FUSE ausente), use `--appimage-extract-and-run`
> ou o script `~/bin/lunuz-appimage.sh` — funciona em qualquer distro.
> Se a GUI faltar dependências, aparece um popup (zenity) explicando o que instalar.

## Comandos (22 no total)

| Categoria | Comandos |
|-----------|----------|
| Arquivos | `ls` `pwd` `cd` `cat` `echo` `mkdir` `rm` `cp` `mv` |
| Busca | `grep` `find` |
| Permissões | `chmod` `chown` |
| Linguagens | `java` (OpenJDK) `cpp` (g++) `python` `node` `shell` |
| Sistema | `openjdk` (toolchain) `distro` (identifica distro + ações disponíveis) `gui` (interface) `--version` |

Exemplos:

```bash
lunuz ls -la /tmp
lunuz cpp main.cpp          # compila e executa C++
lunuz java Main.java        # executa Java (source-launch JDK 11+)
lunuz openjdk               # mostra toolchain OpenJDK (java/javac/JAVA_HOME)
lunuz distro                # identificador de distro + ações disponíveis aqui
lunuz distro --list         # lista todas as ações disponíveis nesta distro
lunuz shell script.sh arg1
lunuz grep -r TODO /home    # busca recursiva (diretórios e binários seguros)
lunuz gui                   # interface gráfica
```

## Instalação dos pacotes

Artefatos pré-compilados ficam em `dist/` (gere-os com
`scripts/make_dist.sh`):

| Formato | Arquivo | Instalação |
|---------|---------|------------|
| Debian/Ubuntu | `lunuz-tools_1.2.0_all.deb` | `sudo apt install ./lunuz-tools_1.2.0_all.deb` |
| Fedora/RHEL | `lunuz-tools-1.2.0-1.noarch.rpm` | `sudo dnf install ./lunuz-tools-1.2.0-1.noarch.rpm` |
| Arch/Manjaro | `lunuz-tools-1.2.0-1-any.pkg.tar.zst` | `sudo pacman -U lunuz-tools-1.2.0-1-any.pkg.tar.zst` |
| Tarballs | `.tar.gz` `.tar.bz2` `.tar.xz` `.tar.zst` `.tar` | extraia e rode `python3 -m lunuz gui` |
| Zip | `lunuz-tools-1.2.0.zip` | igual aos tarballs |
| Flatpak | `org.davi.lunuz-tools.json` / `lunuz.flatpakref` | `flatpak-builder build org.davi.lunuz-tools.json` |
| Snap | `snapcraft.yaml` | `snapcraft` (requer snapd) |
| Repo dnf/yum | `lunuz-tools.repo` | `sudo dnf config-manager --add-repo lunuz-tools.repo` ( hospede o rpm antes) |

Dependências da GUI por distro:

| Distro | Pacotes |
|--------|---------|
| Debian/Ubuntu | `sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91` |
| Fedora/RHEL | `sudo dnf install python3 python3-gobject gtk3 vte291` |
| Arch/Manjaro | `sudo pacman -S python python-gobject gtk3 vte3` |
| openSUSE | `sudo zypper in python3 python3-gobject gtk3 vte-2_91` |
| SteamOS (somente leitura) | use o AppImage com `--appimage-extract-and-run` |

Compiladores/linguagens (opcionais):

```bash
# Debian/Ubuntu: sudo apt install default-jdk g++ nodejs
# Fedora:        sudo dnf install java-21-openjdk-devel gcc-c++ nodejs
# Arch:          sudo pacman -S jdk-openjdk gcc nodejs
# openSUSE:      sudo zypper in java-21-openjdk-devel gcc-c++ nodejs
```

## Testes

Três suítes automatizadas cobrem toda a interface (navegação, busca,
botão voltar, visualização, os 102 itens, a fila de execução com saída
real no terminal, seleção múltipla e todos os diálogos):

```bash
python3 tests/test_gui_programatic.py   # tiles/busca/voltar/toggles + 102 itens
python3 tests/test_terminal_queue.py    # fila real: serialização + progresso
python3 tests/test_gui_dialogs.py       # formulário/seletor/confirmação reais
```

## Estrutura

```
lunuz_tools/
├── lunuz/              # pacote Python (cli.py, tools.py, gui.py, actions.py)
├── tests/              # suítes de teste da interface
├── scripts/
│   └── make_dist.sh    # gera deb, rpm, pkg.tar.zst, tars, zip em dist/
├── dist/               # pacotes gerados
├── lunuz-x86_64.AppImage
├── AppDir/             # fonte do AppImage
├── org.davi.lunuz-tools.json
├── snapcraft.yaml
├── README.md           # inglês
├── README.pt-BR.md     # este arquivo (português)
└── setup.py
~/bin/
├── lunuz               # wrapper Python
├── lunuz.sh            # script shell
├── lunuz-gui           # lançador da interface gráfica
└── lunuz-appimage.sh   # extrai/roda o AppImage sem FUSE
```
