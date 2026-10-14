#!/usr/bin/env python3
"""Core tools for lunuz - Linux-like command line utilities."""

import os
import shutil
import sys
import fnmatch
import subprocess


def ls(path=".", all=False, long_format=False):
    """List directory contents."""
    try:
        entries = os.listdir(path)
        if not all:
            entries = [e for e in entries if not e.startswith(".")]
        
        if long_format:
            for entry in sorted(entries):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    marker = "/"
                elif os.path.islink(entry_path):
                    marker = "@"
                else:
                    marker = ""
                size = os.path.getsize(entry_path)
                print(f"{size:>8} {entry}{marker}")
        else:
            for entry in sorted(entries):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    print(f"{entry}/")
                elif os.path.islink(entry_path):
                    print(f"{entry}@")
                else:
                    print(entry)
    except FileNotFoundError:
        print(f"lunuz: cannot access '{path}': No such file or directory", file=sys.stderr)
        sys.exit(1)


def pwd():
    """Print working directory."""
    print(os.getcwd())


def cd(path):
    """Change directory."""
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"lunuz: cannot change directory to '{path}': No such file or directory", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError:
        print(f"lunuz: cannot change directory to '{path}': Not a directory", file=sys.stderr)
        sys.exit(1)


def cat(files):
    """Concatenate and display files."""
    for file in files:
        try:
            with open(file, "r") as f:
                print(f.read(), end="")
        except FileNotFoundError:
            print(f"lunuz: cannot open '{file}': No such file or directory", file=sys.stderr)
            sys.exit(1)


def echo(text):
    """Display a line of text."""
    print(text)


def mkdir(directories):
    """Make directories."""
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"lunuz: cannot create directory '{directory}': {e}", file=sys.stderr)
            sys.exit(1)


def rm(files, force=False):
    """Remove files or directories."""
    for file in files:
        try:
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
        except FileNotFoundError:
            if not force:
                print(f"lunuz: cannot remove '{file}': No such file or directory", file=sys.stderr)
                sys.exit(1)


def cp(source, destination):
    """Copy files and directories."""
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
    except FileNotFoundError:
        print(f"lunuz: cannot copy '{source}': No such file or directory", file=sys.stderr)
        sys.exit(1)


def mv(source, destination):
    """Move or rename files or directories."""
    try:
        shutil.move(source, destination)
    except FileNotFoundError:
        print(f"lunuz: cannot move '{source}': No such file or directory", file=sys.stderr)
        sys.exit(1)


def grep(pattern, files, ignore_case=False):
    """Search for a pattern in files (directories are searched recursively)."""
    import re
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)

    # Expand directories into their files (recursive search)
    targets = []
    for file in files:
        if os.path.isdir(file):
            for root, _dirs, names in os.walk(file):
                for name in names:
                    targets.append(os.path.join(root, name))
        else:
            targets.append(file)

    for file in targets:
        try:
            # errors="ignore" avoids crashes on binary files
            with open(file, "r", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        print(f"{file}:{line_num}:{line.rstrip()}")
        except FileNotFoundError:
            print(f"lunuz: cannot open '{file}': No such file or directory", file=sys.stderr)
        except (IsADirectoryError, PermissionError, OSError):
            continue


def find(path, name=None, file_type=None):
    """Find files in directory."""
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if name and not fnmatch.fnmatch(file, name):
                    continue
                if file_type == "f" and not os.path.isfile(file_path):
                    continue
                if file_type == "d" and not os.path.isdir(file_path):
                    continue
                print(file_path)
    except FileNotFoundError:
        print(f"lunuz: cannot access '{path}': No such file or directory", file=sys.stderr)
        sys.exit(1)


def chmod(mode, files):
    """Change file permissions."""
    import stat
    for file in files:
        try:
            os.chmod(file, int(mode, 8) if mode.isdigit() else getattr(stat, f'CHMOD_{mode.replace("/", "_").upper()}', None) or int(mode, 8))
            # Simple handling: if numeric, use int(); otherwise try common symbols
        except FileNotFoundError:
            print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        except (ValueError, OSError) as e:
            print(f"lunuz: cannot change permissions of '{file}': {e}", file=sys.stderr)


def chown(owner, files):
    """Change file owner."""
    import pwd
    import grp
    import os as _os
    for file in files:
        try:
            # Parse owner: "user" or "user:group"
            parts = owner.split(":")
            user = parts[0]
            group = parts[1] if len(parts) > 1 else None
            
            u_id = pwd.getpwnam(user).pw_uid if user else None
            g_id = grp.getgrnam(group).gr_gid if group else None
            
            # Get current file stats to preserve existing uid/gid if not changing
            try:
                stat_info = _os.stat(file)
                current_uid = stat_info.st_uid
                current_gid = stat_info.st_gid
            except _OSError:
                current_uid = 0
                current_gid = 0
            
            # Use provided uid/gid or keep current
            final_uid = u_id if u_id is not None else current_uid
            final_gid = g_id if g_id is not None else current_gid
            
            _os.chown(file, final_uid, final_gid)
        except FileNotFoundError:
            print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        except KeyError:
            print(f"lunuz: user/group '{owner}' not found", file=sys.stderr)
        except OSError as e:
            print(f"lunuz: cannot change owner of '{file}': {e}", file=sys.stderr)


# ==================================================================
# Language runners: java, shell, python, node
# ==================================================================

def _find_binary(name, extra_paths=None):
    """Find an executable binary in PATH or common locations."""
    paths = list(extra_paths or [])
    env_path = os.environ.get("PATH", "")
    paths.extend(p for p in env_path.split(":") if p)
    # Common fallbacks per distro (Debian/Ubuntu, Arch, Fedora, openSUSE, SteamOS)
    defaults = ["/usr/bin", "/usr/local/bin", "/bin", "/snap/bin", "/opt/java/bin"]
    paths.extend(defaults)
    seen = set()
    for d in paths:
        if d in seen:
            continue
        seen.add(d)
        candidate = os.path.join(d, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def java(file, compile_only=False):
    """Compile and run a Java file (uses single-file source launch on JDK 11+)."""
    java_bin = _find_binary("java")
    javac_bin = _find_binary("javac")

    if not java_bin and not javac_bin:
        print("lunuz: Java not found. Install a JDK (e.g. default-jdk, jdk-openjdk, java-21-openjdk-devel).", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(file):
        print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        sys.exit(1)

    # JDK 11+ can run .java source files directly
    if java_bin:
        result = subprocess.run([java_bin, file])
        sys.exit(result.returncode)

    # Fallback: javac + java
    if not javac_bin:
        print("lunuz: javac not found but java is; JDK too old for single-file run.", file=sys.stderr)
        sys.exit(1)
    classname = os.path.splitext(os.path.basename(file))[0]
    tmpdir = os.path.dirname(os.path.abspath(file))
    result = subprocess.run([javac_bin, "-d", tmpdir, file])
    if result.returncode != 0:
        sys.exit(result.returncode)
    result = subprocess.run([java_bin, "-cp", tmpdir, classname])
    sys.exit(result.returncode)


def shell(file, args=None):
    """Execute a shell script (bash) with optional arguments."""
    bash_bin = _find_binary("bash")
    if not bash_bin:
        print("lunuz: bash not found.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(file):
        print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run([bash_bin, file] + list(args or []))
    sys.exit(result.returncode)


def python(file):
    """Run a Python script with the current interpreter."""
    if not os.path.isfile(file):
        print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run([sys.executable or "python3", file])
    sys.exit(result.returncode)


def node(file):
    """Run a JavaScript file with node (if available)."""
    node_bin = _find_binary("node")
    if not node_bin:
        print("lunuz: node not found. Install Node.js (e.g. nodejs, nodejs-npm).", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(file):
        print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run([node_bin, file])
    sys.exit(result.returncode)


def cpp(file, keep=False):
    """Compile and run a C++ source file with g++/clang++."""
    compiler = _find_binary("g++") or _find_binary("clang++")
    if not compiler:
        print("lunuz: C++ compiler not found. Install g++ (e.g. g++, build-essential, gcc-c++).", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(file):
        print(f"lunuz: cannot access '{file}': No such file or directory", file=sys.stderr)
        sys.exit(1)

    # Output binary next to source (or temp if no write permission)
    base = os.path.splitext(os.path.abspath(file))[0]
    out_bin = base
    if not os.access(os.path.dirname(os.path.abspath(file)), os.W_OK):
        import tempfile
        out_bin = os.path.join(tempfile.gettempdir(), os.path.basename(base) + "_lunuz")

    result = subprocess.run([compiler, "-std=c++17", "-O2", "-o", out_bin, file])
    if result.returncode != 0:
        sys.exit(result.returncode)

    result = subprocess.run([out_bin])
    rc = result.returncode
    if not keep and out_bin != base:
        try:
            os.remove(out_bin)
        except OSError:
            pass
    sys.exit(rc)


def openjdk(version_only=False):
    """Show OpenJDK toolchain info: java, javac, versions and locations."""
    java_bin = _find_binary("java")
    javac_bin = _find_binary("javac")

    if not java_bin:
        print("OpenJDK: NOT installed", file=sys.stderr)
        print("Install: sudo apt install default-jdk   | sudo dnf install java-21-openjdk-devel"
              "   | sudo pacman -S jdk-openjdk   | sudo zypper in java-21-openjdk-devel", file=sys.stderr)
        sys.exit(1)

    if version_only:
        subprocess.run([java_bin, "-version"])
        sys.exit(0)

    def ver(binary):
        if not binary:
            return "(not found)"
        try:
            r = subprocess.run([binary, "-version"], capture_output=True, text=True)
            first = (r.stderr or r.stdout).splitlines()
            return first[0] if first else "(unknown)"
        except OSError:
            return "(error)"

    print("=== OpenJDK Toolchain ===")
    print(f"  java  : {java_bin}")
    print(f"          {ver(java_bin)}")
    print(f"  javac : {javac_bin or '(not found - JRE only?)'}")
    if javac_bin:
        print(f"          {ver(javac_bin)}")
    # JAVA_HOME hint
    jh = os.environ.get("JAVA_HOME", "")
    if not jh and java_bin:
        jh = os.path.dirname(os.path.dirname(os.path.realpath(java_bin)))
    print(f"  JAVA_HOME: {jh or '(not set)'}")
    sys.exit(0)