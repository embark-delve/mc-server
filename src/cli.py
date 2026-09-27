"""Installed CLI with explicit failure status and no implicit deployment."""

import argparse
import getpass
import json
import sys
import zipfile
from pathlib import Path

import yaml

from src.minecraft_server_manager import MinecraftServerManager
from src.utils.config import Config


def setup_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage private local Minecraft servers"
    )
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--profile")
    parser.add_argument("--base-dir")
    parser.add_argument("--port", type=int)
    parser.add_argument("--memory")
    parser.add_argument("--type", choices=["docker"])
    parser.add_argument("--version")
    parser.add_argument("--flavor", choices=["forge", "paper", "vanilla"])
    parser.add_argument("--debug", action="store_true", default=None)
    parser.add_argument("--disable-auto-shutdown", action="store_true", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create an empty private profile")
    init.add_argument("--accept-eula", action="store_true")
    for cmd in [
        "start",
        "stop",
        "restart",
        "status",
        "security",
        "backup",
        "backups",
        "config",
        "render",
        "mods-list",
    ]:
        sub.add_parser(cmd)
    players = sub.add_parser(
        "players",
        help="Ban/remove Minecraft players, including configured allowlist members",
    )
    player_commands = players.add_subparsers(dest="player_command", required=True)
    player_commands.add_parser("list")
    for operation in ["add", "ban", "unban", "remove"]:
        action = player_commands.add_parser(operation)
        action.add_argument("minecraft_name")
    admin = sub.add_parser(
        "admin", help="Set or replace the single local administrator"
    )
    admin.add_argument("username")
    admin.add_argument("--password-stdin", action="store_true")
    setup = sub.add_parser("setup", help="Prepare a private world with safe defaults")
    setup.add_argument("--minecraft-name", required=True)
    setup.add_argument("--accept-eula", action="store_true")
    web = sub.add_parser("web", help="Open the private, laptop-only family dashboard")
    web.add_argument("--ui-port", type=int, default=8765)
    restore = sub.add_parser(
        "restore", help="Restore a stopped profile, preserving data.rollback"
    )
    restore.add_argument("archive", type=Path)
    restore.add_argument("--confirm-profile", required=True)
    logs = sub.add_parser("logs")
    logs.add_argument("--lines", type=int, default=50)
    console = sub.add_parser("console")
    console.add_argument("text", nargs="+")
    install = sub.add_parser(
        "mods-install", help="Install a reviewed local Forge JAR while stopped"
    )
    install.add_argument("jar", type=Path)
    install.add_argument("--sha256", required=True)
    for operation in ("mods-enable", "mods-disable"):
        toggle = sub.add_parser(operation)
        toggle.add_argument("filename")
    remove = sub.add_parser("mods-remove")
    remove.add_argument("filename")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = setup_argument_parser()
    args = parser.parse_args(argv)
    try:
        config = (
            Config().from_file(args.config).from_env().from_args(vars(args)).validate()
        )
        manager = MinecraftServerManager(config=config)
        command = args.command
        if command == "players":
            if args.player_command == "list":
                print(
                    json.dumps(
                        manager.accounts.players(config.get("server.allowlist")),
                        indent=2,
                    )
                )
            else:
                manager.change_player(args.minecraft_name, args.player_command)
                print(f"{args.player_command} completed for {args.minecraft_name}")
        elif command == "admin":
            password = (
                sys.stdin.readline(1024).rstrip("\r\n")
                if args.password_stdin
                else getpass.getpass("Admin password (15+ characters): ")
            )
            manager.accounts.set_admin(args.username, password)
            print("Single admin configured; previous admin sessions are revoked.")
        elif command == "setup":
            if not args.accept_eula:
                raise ValueError(
                    "Read https://aka.ms/MinecraftEULA and explicitly accept before setup"
                )
            manager.change_player(args.minecraft_name, "add")
            manager.initialize(accept_eula=True)
            print("World prepared. Start it when Docker is ready.")
        elif command == "web":
            from src.web.app import serve

            serve(manager, args.ui_port)
        elif command == "init":
            manager.initialize(accept_eula=args.accept_eula)
            print(f"Initialized {config.get('profile')}: {manager.base_dir}")
        elif command == "config":
            print(yaml.safe_dump(config.get_all(), sort_keys=False))
        elif command == "render":
            print(yaml.safe_dump(manager.compose_config(), sort_keys=False))
        elif command in ("start", "stop", "restart"):
            if not getattr(manager, command)():
                raise RuntimeError(f"{command} failed")
            print(f"{command} completed for {config.get('profile')}")
        elif command == "security":
            print(json.dumps(manager.verify_security(), indent=2))
        elif command == "status":
            print(json.dumps(manager.status(), indent=2))
        elif command == "logs":
            print("\n".join(manager.get_logs(args.lines)))
        elif command == "console":
            print(manager.execute_command(" ".join(args.text)))
        elif command == "backup":
            print(manager.backup())
        elif command == "backups":
            from src.utils.file_manager import FileManager

            for path in FileManager.list_backups(manager.backup_dir):
                print(path)
        elif command == "restore":
            if args.confirm_profile != config.get("profile"):
                raise ValueError("Confirmation must match the target profile name")
            manager.restore(args.archive)
            print(
                "Restored. Previous data retained as data.rollback; verify before removing it"
            )
        elif command == "mods-install":
            manager.install_local_mod(args.jar, args.sha256)
            print(
                "Installed; complete runtime and dependency validation before normal play"
            )
        elif command in ("mods-enable", "mods-disable"):
            manager.set_mod_enabled(args.filename, command == "mods-enable")
            print("Mod state updated. Verify dependencies before starting.")
        elif command == "mods-remove":
            manager.uninstall_mod(args.filename)
        elif command == "mods-list":
            print(json.dumps(manager.list_mods(), indent=2))
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        zipfile.BadZipFile,
        yaml.YAMLError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
