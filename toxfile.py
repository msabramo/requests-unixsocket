"""Project-local tox env customizations."""

import platform
import ssl
from base64 import b64encode
from hashlib import sha256
from logging import getLogger
from os import environ, getenv
from pathlib import Path

from tox.execute.request import StdinSource
from tox.plugin import impl
from tox.tox_env.api import ToxEnv


IS_GITHUB_ACTIONS_RUNTIME = getenv('GITHUB_ACTIONS') == 'true'
FILE_APPEND_MODE = 'a'
UNICODE_ENCODING = 'utf-8'
SYS_PLATFORM = platform.system()
IS_WINDOWS = SYS_PLATFORM == 'Windows'


logger = getLogger(__name__)


def _log_debug_before_run_commands(msg: str) -> None:
    logger.debug(
        '%s%s> %s',  # noqa: WPS323
        'toxfile',
        ':tox_before_run_commands',
        msg,
    )


def _log_info_before_run_commands(msg: str) -> None:
    logger.info(
        '%s%s> %s',  # noqa: WPS323
        'toxfile',
        ':tox_before_run_commands',
        msg,
    )


def _log_warning_before_run_commands(msg: str) -> None:
    logger.warning(
        '%s%s> %s',  # noqa: WPS323
        'toxfile',
        ':tox_before_run_commands',
        msg,
    )


@impl
def tox_before_run_commands(tox_env: ToxEnv) -> None:  # noqa: WPS210, WPS213
    """Display test runtime info when in GitHub Actions CI/CD.

    This also injects ``SOURCE_DATE_EPOCH`` env var into build-dists.

    :param tox_env: A tox environment object.
    """
    if tox_env.name == 'build-dists':
        _log_debug_before_run_commands(
            'Setting the Git HEAD-based epoch for reproducibility in GHA...',
        )
        git_executable = 'git'
        git_log_cmd = (  # noqa: WPS317
            git_executable,
            '-c',
            'core.pager=',  # prevents ANSI escape sequences
            'log',
            '-1',
            '--pretty=%ct',  # noqa: WPS323
        )
        tox_env.conf['allowlist_externals'].append(git_executable)
        git_log_outcome = tox_env.execute(git_log_cmd, StdinSource.OFF)
        tox_env.conf['allowlist_externals'].pop()
        if git_log_outcome.exit_code:
            _log_warning_before_run_commands(
                f'Failed to look up Git HEAD timestamp. {git_log_outcome!s}',
            )
            return

        git_head_timestamp = git_log_outcome.out.strip()

        _log_info_before_run_commands(
            f'Setting `SOURCE_DATE_EPOCH={git_head_timestamp!s}` environment '
            'variable to facilitate build reproducibility...',
        )
        tox_env.environment_variables['SOURCE_DATE_EPOCH'] = git_head_timestamp

    if tox_env.name not in {'py', 'python'} or not IS_GITHUB_ACTIONS_RUNTIME:
        _log_debug_before_run_commands(
            'Not logging runtime info because this is not a test run on '
            'GitHub Actions platform...',
        )
        return

    _log_info_before_run_commands('INFO Logging runtime details...')

    systeminfo_executable = 'systeminfo'
    systeminfo_cmd = (systeminfo_executable,)
    if IS_WINDOWS:
        tox_env.conf['allowlist_externals'].append(systeminfo_executable)
        tox_env.execute(systeminfo_cmd, stdin=StdinSource.OFF, show=True)
        tox_env.conf['allowlist_externals'].pop()
    else:
        _log_debug_before_run_commands(
            f'Not running {systeminfo_executable!s} because this is '
            'not Windows...',
        )

    _log_info_before_run_commands('Logging platform information...')
    print(  # noqa: T201, WPS421
        'Current platform information:\n'
        f'{platform.platform()=}'
        f'{platform.system()=}'
        f'{platform.version()=}'
        f'{platform.uname()=}'
        f'{platform.release()=}',
    )

    _log_info_before_run_commands('Logging current OpenSSL module...')
    print(  # noqa: T201, WPS421
        'Current OpenSSL module:\n'
        f'{ssl.OPENSSL_VERSION=}\n'
        f'{ssl.OPENSSL_VERSION_INFO=}\n'
        f'{ssl.OPENSSL_VERSION_NUMBER=}',
    )


def _log_debug_after_run_commands(msg: str) -> None:
    logger.debug(
        '%s%s> %s',  # noqa: WPS323
        'toxfile',
        ':tox_after_run_commands',
        msg,
    )


def _compute_sha256sum(file_path: Path) -> str:
    return sha256(file_path.read_bytes()).hexdigest()


def _produce_sha256sum_line(file_path: Path) -> str:
    sha256_str = _compute_sha256sum(file_path)
    return f'{sha256_str!s}  {file_path.name!s}'


@impl
def tox_after_run_commands(tox_env: ToxEnv) -> None:
    """Compute combined dists hash post build-dists under GHA.

    :param tox_env: A tox environment object.
    """
    if tox_env.name == 'build-dists' and IS_GITHUB_ACTIONS_RUNTIME:
        _log_debug_after_run_commands(
            'Computing and storing the base64 representation '
            'of the combined dists SHA-256 hash in GHA...',
        )
        dists_dir_path = Path(__file__).parent / 'dist'
        emulated_sha256sum_output = '\n'.join(
            _produce_sha256sum_line(artifact_path)
            for artifact_path in dists_dir_path.glob('*')
        )
        emulated_base64_w0_output = b64encode(
            emulated_sha256sum_output.encode(),
        ).decode()

        with Path(environ['GITHUB_OUTPUT']).open(
            encoding=UNICODE_ENCODING,
            mode=FILE_APPEND_MODE,
        ) as outputs_file:
            print(  # noqa: T201, WPS421
                'combined-dists-base64-encoded-sha256-hash='
                f'{emulated_base64_w0_output!s}',
                file=outputs_file,
            )


def tox_append_version_info() -> str:
    """Produce text to be rendered in ``tox --version``.

    :returns: A string with the plugin details.
    """
    return '[toxfile]'  # Broken: https://github.com/tox-dev/tox/issues/3508
