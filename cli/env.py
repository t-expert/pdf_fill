import os
import sys

from dotenv import dotenv_values, load_dotenv


def get_sandbox_env(args):
    if args.env:
        return args.env
    env = (
        'dev'
        if args.dev
        else 'test'
        if args.test
        else 'prod'
        if args.prod
        else 'prod-backup'
        if args.prod_backup
        else None
    )
    if not env:
        raise ValueError('Env is not specified. The validation of env does not work somehow')
    return env


def load_sandbox_env(args):
    env = get_sandbox_env(args)
    return SandboxEnv(env)


def export_sandbox_env(args):
    sandbox_env = load_sandbox_env(args)
    sandbox_env.export(args.home, args.last_commit_hash, args.app_version)


class SandboxEnv:
    env = 'dev'
    evars = {}

    def __init__(self, env):
        self.validate(env)
        self.env = env.lower()
        self.read()

    def validate(self, env):
        """Validate the environment value.

        Args:
            env (str): Environment name to validate

        Returns:
            bool: True if valid, raises ValueError if invalid

        Raises:
            ValueError: If environment is not in allowed list
        """
        allowed_environments = ['dev', 'test', 'prod', 'prod-backup']

        if env.lower() not in allowed_environments:
            raise ValueError(
                f'Invalid environment: {env}. Must be one of: {", ".join(allowed_environments)}'
            )
        return True

    def read(self):
        """Read environment variables from env files.

        Reads variables from both environment-specific file (e.g., .env.dev)
        and .env file. Variables in .env will override those in environment-specific files.

        Returns:
            dict: Environment variables
        """
        env_file = f'.env.{self.env}'
        env_specific_vars = {}

        try:
            load_dotenv(env_file)
            env_specific_vars = dotenv_values(env_file)
        except Exception:
            print(f'Warning: Environment file {env_file} not found', file=sys.stderr)

        self.evars.update(env_specific_vars)

        # .env file stores sensitive secrets
        # We only load them into the environment variables, without storing them in evars.
        if self.env == 'prod':
            load_dotenv('.secrets')
        elif self.env == 'prod-backup':
            load_dotenv('.secrets-backup')

    def get(self, name):
        value = os.getenv(name)
        if not value:
            raise ValueError(f'Env {name} not found')
        return value

    def export(self, home, last_commit_hash, app_version):
        """Export environment variables to a specified home directory's .env file.

        Args:
            home (str): Path to the home directory where .env should be created/updated

        Raises:
            ValueError: If home directory is invalid or not writable
        """
        from pathlib import Path

        # Convert home to Path object and resolve to absolute path
        home_path = Path(home).expanduser().resolve()

        # Validate home directory
        if not home_path.exists():
            raise ValueError(f'Home directory does not exist: {home}')
        if not home_path.is_dir():
            raise ValueError(f'Path is not a directory: {home}')

        # Create .env file path
        env_file = home_path / '.env'

        # Create parent directories if they don't exist
        env_file.parent.mkdir(parents=True, exist_ok=True)

        # Track last commit hash in env
        self.evars['LAST_COMMIT_HASH'] = last_commit_hash
        # Track current app version
        if app_version:
            self.evars['APP_VERSION'] = app_version

        # Write variables to file
        try:
            with open(env_file, 'w') as f:
                for key, value in self.evars.items():
                    f.write(f'export {key}={value}\n')
        except PermissionError:
            raise ValueError(f'Cannot write to {env_file}. Permission denied.')
