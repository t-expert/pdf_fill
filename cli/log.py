import subprocess

from .env import load_sandbox_env


def print_sandbox_logs(args):
    load_sandbox_env(args)
    sandbox_id = args.sandbox_id
    subprocess.run(['e2b', 'auth', 'logout'], text=True, check=True)
    subprocess.run(['e2b', 'sbx', 'logs', sandbox_id], text=True, check=True)
