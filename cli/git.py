import subprocess


def get_current_commit_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
