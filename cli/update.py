import os
import subprocess

from .env import SandboxEnv, get_sandbox_env
from .git import get_current_commit_hash
from .spawn import SandboxSpawner
from .version import get_previous_version, get_version_from_tag


def update_template(args):
    env = get_sandbox_env(args)
    return _update_template_impl(env, args.dir or '.', False, args.skip_check)


def rollback_template(args):
    env = get_sandbox_env(args)
    return _update_template_impl(env, args.dir or '.', True)


def _update_template_impl(env: str, dir, rollback=False, skip=False):
    sandbox_dir = os.path.realpath(os.path.join(os.getcwd(), dir))
    if not sandbox_dir.endswith('/manus-sandbox/sandbox'):
        raise ValueError('Sandbox Cli must be executed in path /sandbox')
    if rollback:
        # Get and checkout the previous version
        prev_version = get_previous_version()
        print(f'Rolling back to version: {prev_version}')

        # Get the commit hash for the previous version tag
        commit_hash = (
            subprocess.check_output(['git', 'rev-list', '-n', '1', prev_version]).decode().strip()
        )

        # Checkout the specific commit
        subprocess.run(['git', 'checkout', commit_hash], check=True)

    print('running pyarmor')

    e2b_config_dir_path = os.path.join(sandbox_dir, 'e2b')
    sandbox_runtime_dir = os.path.join(sandbox_dir, 'sandbox-runtime')
    os.chdir(sandbox_runtime_dir)
    subprocess.run(['pipenv', 'run', './build.sh'], check=True)
    subprocess.run(['e2b', 'auth', 'logout'], check=True)

    def update_template(env, version=None):
        # Reset sandbox env
        os.chdir(sandbox_dir)
        SandboxEnv(env)
        e2b_config_path = os.path.join(e2b_config_dir_path, f'{env}.toml')
        command = [
            'e2b',
            'template',
            'build',
            '--config',
            e2b_config_path,
            '-p',
            sandbox_dir,
            '--build-arg',
            f'APP_ENV={env}',
            f'LAST_COMMIT_HASH={get_current_commit_hash()}',
        ]
        if version:
            command.append(f'APP_VERSION={version}')

        subprocess.run(
            command,
            check=True,
        )

    def update_production_template():
        version = get_version_from_tag()
        print(f'Updating to version: {version}')
        if not rollback and not skip:
            print('Updating dev template to verify sandbox availability')
            update_template('dev')
            spawner = SandboxSpawner(SandboxEnv('dev'))
            success = spawner.spawn(False)
            if not success:
                print('Sandbox fails to health checking. Exit')
                return

        print('Starting to update prod template.')
        update_template('prod', version)

    if env != 'prod':
        update_template(env)
    else:
        update_production_template()
