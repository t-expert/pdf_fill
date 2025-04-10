#!/usr/bin/env python3

import argparse

from .connect import connect_to_sandbox
from .env import export_sandbox_env
from .log import print_sandbox_logs
from .spawn import spawn_sandbox
from .update import rollback_template, update_template


def add_env_args(parser: argparse.ArgumentParser):
    env_group = parser.add_mutually_exclusive_group(required=True)
    env_group.add_argument(
        '--env', choices=['dev', 'test', 'prod', 'prod-backup'], help='Specify target environment'
    )
    env_group.add_argument('--dev', action='store_true', help='Use development environment')
    env_group.add_argument('--test', action='store_true', help='Use testing environment')
    env_group.add_argument('--prod', action='store_true', help='Use production environment')
    env_group.add_argument(
        '--prod-backup', action='store_true', help='Use production backup environment'
    )


def add_dir_arg(parser):
    parser.add_argument('--dir', '-d', help='Specify sandbox directory path')


def add_home_arg(parser):
    parser.add_argument('--home', help='Specify home directory path (default: ~)', default='~')


def add_last_commit_hash(parser):
    parser.add_argument(
        '--last-commit-hash', help='Track the last commit hash of this version', required=True
    )


def add_app_version_arg(parser):
    parser.add_argument('--app-version', help='Track the current app version')


def add_sandbox_id(parser):
    parser.add_argument('--sandbox-id', '--sid', help='Specify sandbox identifier', required=True)


def add_skip_check_arg(parser):
    parser.add_argument(
        '--skip-check',
        '--skip',
        action='store_true',
        help='Skip development sandbox verification before production update',
    )


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(
        description='Sandbox CLI - A command line tool for sandbox management', prog='sbx'
    )

    parser.add_argument('--dir', '-d', help='sandbox dir')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    export_parser = subparsers.add_parser(
        'export', help='Export all environment variables from project files to $HOME/.env'
    )
    export_parser.set_defaults(func=export_sandbox_env)
    add_env_args(export_parser)
    add_home_arg(export_parser)
    add_last_commit_hash(export_parser)
    add_app_version_arg(export_parser)

    update_parser = subparsers.add_parser('update', help='Update sandbox template version')
    update_parser.set_defaults(func=update_template)
    add_env_args(update_parser)
    add_dir_arg(update_parser)
    add_skip_check_arg(update_parser)

    # Create parser for the "spawn" command
    spawn_parser = subparsers.add_parser('spawn', help='Spawn a new sandbox')
    spawn_parser.set_defaults(func=spawn_sandbox)
    spawn_parser.add_argument(
        '--long',
        action='store_true',
        help='Set sandbox timeout to 30 minutes instead of default 5 minutes',
    )
    add_env_args(spawn_parser)

    # Create parser for the "connect" command
    connect_parser = subparsers.add_parser(
        'connect', help='Connect to a specific sandbox using its identifier'
    )
    connect_parser.set_defaults(func=connect_to_sandbox)
    add_sandbox_id(connect_parser)
    add_env_args(connect_parser)

    # Create parser for the "log" command
    log_parser = subparsers.add_parser('logs', help='Display logs for the specified sandbox')
    log_parser.set_defaults(func=print_sandbox_logs)
    add_sandbox_id(log_parser)
    add_env_args(log_parser)

    # Create parser for the "rollback" command
    rollback_parser = subparsers.add_parser(
        'rollback', help='Revert sandbox to previous template version'
    )
    rollback_parser.set_defaults(func=rollback_template)
    add_env_args(rollback_parser)
    add_dir_arg(rollback_parser)

    # Parse arguments and execute the appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
