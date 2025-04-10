import subprocess

from .env import load_sandbox_env


def connect_to_sandbox(args):
    load_sandbox_env(args)
    sandbox_id = args.sandbox_id
    subprocess.run(['e2b', 'auth', 'logout'], text=True, check=True)
    subprocess.run(['e2b', 'sbx', 'connect', sandbox_id], text=True, check=True)
