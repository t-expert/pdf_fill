import subprocess

from packaging import version


def is_valid_version(version_str: str):
    try:
        version.Version(version_str)
        return True
    except Exception:
        return False


def get_version_from_tag() -> str:
    """Extract version number from the last git tag.

    Returns:
        str: Version number in format 'x.y.z'

    Raises:
        ValueError: If no valid version tag is found
    """
    try:
        # Get the most recent tag
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'], capture_output=True, text=True, check=True
        )
        version_tag = result.stdout.strip()
        # Validate version format (x.y.z)
        sandbox_version = version.Version(version_tag).public
        return sandbox_version

    except subprocess.CalledProcessError as e:
        raise ValueError(
            'No version tag found. Please tag your last commit with a version number'
        ) from e


def get_previous_version() -> str:
    """Get the second-last version tag from git history.

    Returns:
        str: Previous version number in format 'x.y.z'

    Raises:
        VersionError: If no previous version tag is found
    """
    try:
        # Get all tags sorted by version
        result = subprocess.run(
            ['git', 'tag', '--sort=refname'], capture_output=True, text=True, check=True
        )

        tags = result.stdout.strip().split('\n')

        # Filter valid version tags
        version_tags = [tag for tag in tags if is_valid_version(tag)]

        if len(version_tags) < 2:
            raise ValueError('No previous version tag found')

        # Get second tag (previous version)
        previous_tag = version_tags[1]

        return previous_tag

    except (subprocess.CalledProcessError, IndexError) as e:
        raise ValueError('Failed to get previous version tag') from e
