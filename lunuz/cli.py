#!/usr/bin/env python3
"""lunuz tools - A collection of Linux-like command line utilities."""

import sys
import os
import argparse

try:
    from . import __version__
except ImportError:
    __version__ = "1.2.0"


def main():
    parser = argparse.ArgumentParser(
        prog="lunuz",
        description="lunuz tools - A collection of Linux-like command line utilities",
    )
    parser.add_argument("--version", action="version", version=f"lunuz {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # =========== ls command ===========
    ls_parser = subparsers.add_parser("ls", help="List directory contents")
    ls_parser.add_argument(
        "path", nargs="?", default=".", help="Path to list (default: current directory)"
    )
    ls_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Show hidden files",
    )
    ls_parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Use long listing format",
    )

    # =========== pwd command ===========
    subparsers.add_parser("pwd", help="Print working directory")

    # =========== cd command ===========
    cd_parser = subparsers.add_parser("cd", help="Change directory")
    cd_parser.add_argument("path", help="Directory to change to")

    # =========== cat command ===========
    cat_parser = subparsers.add_parser("cat", help="Concatenate and display files")
    cat_parser.add_argument("files", nargs="+", help="Files to display")

    # =========== echo command ===========
    echo_parser = subparsers.add_parser("echo", help="Display a line of text")
    echo_parser.add_argument("text", nargs="+", help="Text to display")

    # =========== mkdir command ===========
    mkdir_parser = subparsers.add_parser("mkdir", help="Make directories")
    mkdir_parser.add_argument("directories", nargs="+", help="Directories to create")

    # =========== rm command ===========
    rm_parser = subparsers.add_parser("rm", help="Remove files or directories")
    rm_parser.add_argument("files", nargs="+", help="Files or directories to remove")
    rm_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ignore nonexistent arguments and never prompt",
    )

    # =========== cp command ===========
    cp_parser = subparsers.add_parser("cp", help="Copy files and directories")
    cp_parser.add_argument("source", help="Source file or directory")
    cp_parser.add_argument("destination", help="Destination file or directory")

    # =========== mv command ===========
    mv_parser = subparsers.add_parser("mv", help="Move or rename files or directories")
    mv_parser.add_argument("source", help="Source file or directory")
    mv_parser.add_argument("destination", help="Destination file or directory")

    # =========== grep command ===========
    grep_parser = subparsers.add_parser("grep", help="Search text in files")
    grep_parser.add_argument("pattern", help="Text pattern to search")
    grep_parser.add_argument("files", nargs="+", help="Files to search")
    grep_parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Ignore case distinctions",
    )
    grep_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search directories recursively (always on - flag accepted for familiarity)",
    )

    # =========== find command ===========
    find_parser = subparsers.add_parser("find", help="Find files in directory")
    find_parser.add_argument("path", help="Directory to search")
    find_parser.add_argument("-name", dest="name", help="Filter by filename pattern")
    find_parser.add_argument("-type", dest="type", help="Filter by file type (f=file, d=directory)")

    # =========== chmod command ===========
    chmod_parser = subparsers.add_parser("chmod", help="Change file permissions")
    chmod_parser.add_argument("mode", help="Permission mode (e.g., 755, +x, -r)")
    chmod_parser.add_argument("files", nargs="+", help="Files to change permissions")

    # =========== chown command ===========
    chown_parser = subparsers.add_parser("chown", help="Change file owner")
    chown_parser.add_argument("owner", help="User or user:group")
    chown_parser.add_argument("files", nargs="+", help="Files to change ownership")

    # =========== java command ===========
    java_parser = subparsers.add_parser("java", help="Compile and run a Java file")
    java_parser.add_argument("file", help="Java source file (.java)")

    # =========== shell command ===========
    shell_parser = subparsers.add_parser("shell", help="Execute a shell script (bash)")
    shell_parser.add_argument("file", help="Shell script file (.sh)")
    shell_parser.add_argument("args", nargs="*", help="Arguments passed to the script")

    # =========== python command ===========
    python_parser = subparsers.add_parser("python", help="Run a Python script")
    python_parser.add_argument("file", help="Python file (.py)")

    # =========== node command ===========
    node_parser = subparsers.add_parser("node", help="Run a JavaScript file (Node.js)")
    node_parser.add_argument("file", help="JavaScript file (.js)")

    # =========== cpp command ===========
    cpp_parser = subparsers.add_parser("cpp", help="Compile and run a C++ file (g++)")
    cpp_parser.add_argument("file", help="C++ source file (.cpp/.cc/.cxx)")
    cpp_parser.add_argument("-k", "--keep", action="store_true", help="Keep the compiled binary")

    # =========== openjdk command ===========
    openjdk_parser = subparsers.add_parser("openjdk", help="Show OpenJDK toolchain info")
    openjdk_parser.add_argument("--version", "-v", action="store_true", help="Only show java version")

    # =========== gui command ===========
    distro_parser = subparsers.add_parser(
        "distro", help="Identify the distro and which actions are available here")
    distro_parser.add_argument("-l", "--list", action="store_true",
                               help="List every action available on this distro")

    subparsers.add_parser("gui", help="Launch the graphical interface (LinuxToys-style)")

    args = parser.parse_args()

    if not args.command:
        # sem argumentos (menu de aplicativos / duplo clique): abre a GUI
        try:
            from . import gui
            gui.main()
            return
        except ImportError:
            # sem GTK/VTE disponível: mostra a ajuda em vez de falhar em silêncio
            parser.print_help()
            sys.exit(1)

    if args.command == "ls":
        from . import tools
        tools.ls(args.path, all=args.all, long_format=args.long)
    elif args.command == "pwd":
        from . import tools
        tools.pwd()
    elif args.command == "cd":
        from . import tools
        tools.cd(args.path)
    elif args.command == "cat":
        from . import tools
        tools.cat(args.files)
    elif args.command == "echo":
        from . import tools
        tools.echo(" ".join(args.text))
    elif args.command == "mkdir":
        from . import tools
        tools.mkdir(args.directories)
    elif args.command == "rm":
        from . import tools
        tools.rm(args.files, force=args.force)
    elif args.command == "cp":
        from . import tools
        tools.cp(args.source, args.destination)
    elif args.command == "mv":
        from . import tools
        tools.mv(args.source, args.destination)
    elif args.command == "grep":
        from . import tools
        tools.grep(args.pattern, args.files, ignore_case=args.ignore_case)
    elif args.command == "find":
        from . import tools
        tools.find(args.path, name=args.name, file_type=args.type)
    elif args.command == "chmod":
        from . import tools
        tools.chmod(args.mode, args.files)
    elif args.command == "chown":
        from . import tools
        tools.chown(args.owner, args.files)
    elif args.command == "java":
        from . import tools
        tools.java(args.file)
    elif args.command == "shell":
        from . import tools
        tools.shell(args.file, args.args)
    elif args.command == "python":
        from . import tools
        tools.python(args.file)
    elif args.command == "node":
        from . import tools
        tools.node(args.file)
    elif args.command == "cpp":
        from . import tools
        tools.cpp(args.file, keep=args.keep)
    elif args.command == "openjdk":
        from . import tools
        tools.openjdk(version_only=args.version)
    elif args.command == "distro":
        from . import actions
        print(actions.distro_report(list_available=args.list))
    elif args.command == "gui":
        from . import gui
        gui.main()


if __name__ == "__main__":
    main()