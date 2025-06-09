"""Job to get configs from forward networks."""

import re
import time
import typing as t
from base64 import b64encode
from datetime import datetime
from logging import Logger
from os import environ
from pathlib import Path
from urllib.parse import quote

import pytz
from django.db import transaction
from django.db.models import Q
from django.db.models.manager import BaseManager
from django.db.utils import OperationalError
from git.cmd import Git
from git.exc import GitCommandError
from git.index.base import IndexFile
from git.remote import Remote
from git.repo.base import Repo
from git.util import IterableList
from jinja2 import Template
from jinja2.exceptions import UndefinedError
from nautobot.apps.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot.apps.jobs import BooleanVar, ChoiceVar, Job, MultiObjectVar, ObjectVar
from nautobot.core.celery import register_jobs
from nautobot.dcim.models import Device, DeviceType, Location, Platform
from nautobot.extras.models import (
    GitRepository,
    SecretsGroup,
    SecretsGroupAssociation,
    Status,
    Tag,
)
from nautobot_golden_config.models import (
    ConfigRemove,
    ConfigReplace,
    GoldenConfig,
    GoldenConfigSetting,
)
from requests import Response, request
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, JSONDecodeError, SSLError
from requests.sessions import Session
from urllib3.util import Retry

# pylint: disable=no-member, protected-access, too-many-arguments


# Utility Functions
def get_environment_variable(environment_variable: str) -> str:
    """Get environment variable.

    Args:
        environment_variable (str): Name of the environment variable.

    Returns:
        str: Value of the environment variable.
    """
    env_var_value: t.Union[str, None] = environ.get(environment_variable)

    if not env_var_value:
        raise ValueError(f"Missing environment variable: {environment_variable}")

    if env_var_value.endswith("\r"):
        return env_var_value[:-1]

    return env_var_value


def format_base_url_with_params(
    base_url: str,
    parameters: str,
) -> str:
    """Format base url with parameters.

    Args:
        base_url (str): Base url to format.
        parameters (str): Parameters to format with.

    Returns:
        str: Formatted url.
    """
    if not base_url or not parameters:
        raise ValueError("Base or parameters not passed, can not properly format url.")

    if base_url.endswith("/"):
        base_url = base_url[:-1]

    if parameters.startswith("/"):
        parameters = parameters[1:]

    return f"{base_url}/{parameters}"


def check_repository_secrets_group(repository: GitRepository) -> bool:
    """Check if repository has secrets group.

    Args:
        repository (GitRepository): The GitRepository to check.

    Raises:
        ValueError: Repository is not an instance of GitRepository.
        ValueError: Repository does not have either
                    username and token or secrets_group.

    Returns:
        bool: True if the repository has secrets group, False otherwise.
    """
    has_secrets_group = False

    if repository.secrets_group:
        has_secrets_group = True

    return has_secrets_group


def parse_credentials(credentials: SecretsGroup) -> tuple[str, str]:
    """Parse credentials from secrets group.

    Args:
        credentials (SecretsGroup): The SecretsGroup to parse.

    Raises:
        ValueError: If the credentials cannot be parsed.

    Returns:
        Tuple[str, str]: The username and password.
    """
    try:
        username = credentials.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
        )
        password = credentials.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        )
        return username, password
    except SecretsGroupAssociation.DoesNotExist as e:
        raise SecretsGroupAssociation.DoesNotExist(
            "SecretsGroupAssociation TYPE_HTTP or TYPE_USERNAME/TYPE_TOKEN does not exist in the SecretsGroup"
        ) from e


def base_64_encode_credentials(username: str, password: str) -> str:
    """Encode username and password into base64.

    Args:
        username (str): The username to encode.
        password (str): The password to encode.

    Returns:
        str: Base64 encoded credentials.

    Raises:
        ValueError: If username or password is not a string.
    """
    if not username or not password:
        raise ValueError("Username and/or password not passed, can't encode.")

    credentials_str: bytes = f"{username}:{password}".encode(encoding="utf-8")
    return f"Basic {b64encode(s=credentials_str).decode(encoding='utf-8')}"


# Git Utility Class
class GitBase:  # pylint: disable=too-many-instance-attributes
    """Base Git class to help with git actions."""

    def __init__(
        self,
        repository: GitRepository,
        debug: bool,
        logger: Logger,
    ) -> None:
        """Initialize GitBase class.

        Args:
            repository (GitRepository): The GitRepository to use.
            debug (bool): Enable debug mode.
            logger (Logger): The logger to use.
        """
        if not isinstance(logger, Logger):
            raise ValueError("logger must be an instance of logging.Logger")

        self.debug: bool = debug
        self.logger: Logger = logger

        self.path: str = repository.filesystem_path
        self.url: str = repository.remote_url
        self.token: str = ""
        self.token_user: str = ""

        if check_repository_secrets_group(repository=repository):
            repository_secrets_group: SecretsGroup = repository.secrets_group
            self.token_user, self.token = parse_credentials(
                credentials=repository_secrets_group
            )

            if self.debug:
                self.logger.info("Parsing repository secrets group.")
        else:
            self.logger.warning("This is a public repository.")

        if self.token_user and self.token not in self.url:
            quoted_username: str = quote(string=str(self.token_user), safe="")
            quoted_token: str = quote(string=str(self.token), safe="")

            # Some Git Providers require a user as well as a token.
            if self.token_user:
                self.url = re.sub(
                    pattern="//",
                    repl=f"//{quoted_username}:{quoted_token}",
                    string=self.url,
                )
            else:
                # Github only requires the token.
                self.url = re.sub(
                    pattern="//",
                    repl=f"//{quoted_token}@",
                    string=self.url,
                )

        self.branch: str = repository.branch
        self.repository: GitRepository = repository

        if Path(self.path).exists():
            self.repo: Repo = Repo(path=self.path)
        else:
            self.repo: Repo = Repo.clone_from(url=self.url, to_path=self.path)

        self.git_session: Git = self.repo.git
        self.git_session.update_environment(GIT_TERMINAL_PROMPT="0")

        self.git_remotes: IterableList[Remote] = self.repo.remotes
        self.git_origin: Remote = self.repo.remotes.origin

        if self.url not in self.git_origin.urls:
            self.git_origin.set_url(new_url=self.url)

        self.git_index: IndexFile = self.repo.index

    def configure_user_settings(self) -> None:
        """Configure local git user settings if not set."""
        if not self.token_user:
            return
        git_email: str = re.sub(
            pattern=r"\s",
            repl="-",
            string=self.token_user,
        )
        git_config: list[str] = self.git_session.config("--local", "--list")

        if "user.email" not in git_config or "user.name" not in git_config:
            self.git_session.config("--local", "user.name", self.token_user)
            self.git_session.config("--local", "user.email", git_email)
            if self.debug:
                self.logger.info("Configured local git email and/or name.")

    def switch_to_branch(self) -> None:
        """Implemented in Git service class."""
        pass

    def clean_unmerged_files_from_local(self) -> None:
        """When there are conflicts, this will favor remote changes."""
        status: str = self.git_session.status()
        if "unmerged paths" in status:
            self.logger.info("Unmerged files found. Resolving conflicts...")
            conflicting_files: list[str] = []
            for line in status.splitlines():
                if "both modified" in line:
                    conflicting_files.append(
                        line.split(sep="both modified: ")[1].strip()
                    )

            for file in conflicting_files:
                self.git_session.checkout("--ours", file)

            self.git_session.add("-A")
            self.git_session.merge("--continue")
            self.git_index.commit(message=f"Merged with branch {self.branch}")

    def sync_head_with_remote(self) -> None:
        """Sync with remote and move HEAD to remote's HEAD."""
        self.logger.info(f"Synching {self.branch} with remote.")
        self.git_session.fetch("origin", self.branch)
        self.git_session.reset("--hard", f"origin/{self.branch}")

    def merge_with_remote(self) -> None:
        """Implemented in Git service class."""
        pass

    def configure_local_git_repository(self) -> None:
        """Configure local git repository."""
        self.configure_user_settings()
        self.switch_to_branch()
        self.sync_head_with_remote()

    def split_commits_in_batches(
        self,
        commit_description: str,
        batch_size: int = 500,
    ) -> None:
        """Split commits into batches when a single push is too large.

        Args:
            commit_description (str): Commit message
            batch_size (int, optional): Batch size per commit. Defaults to 500.
        """
        modified_files: list[str] = self.repo.untracked_files
        batches = [
            modified_files[batch : (batch + batch_size)]
            for batch in range(0, len(modified_files), step=batch_size)
        ]

        for num, batch in enumerate(iterable=batches):
            self.git_session.add(batch)
            commit_message = (
                f"Partial commit {num + 1}/{len(batches)} - {commit_description}"
            )
            self.git_index.commit(message=commit_message)
            self.git_session.push("origin", self.branch)
            self.logger.info(f"Pushed partial commit {num + 1}/{len(batches)}")
        self.logger.info("Finished backing up devices!")

    def push(self, commit_description: str, batch_size: int = 500) -> None:
        """Implemented in Git service class."""
        pass


class GitLab(GitBase):
    """GitLab Repo object to help with git actions."""

    def __init__(
        self,
        repository: GitRepository,
        debug: bool,
        logger: Logger,
    ) -> None:
        """Initialize GitLab class.

        Args:
            repository (GitRepository): The GitRepository to use.
            debug (bool): Enable debug mode.
            logger (Logger): The logger to use.
        """
        super().__init__(
            repository=repository,
            debug=debug,
            logger=logger,
        )

    def switch_to_branch(self) -> None:
        """Switch local to selected branch.

        Raises:
            GitCommandError: If the branch doesn't exist in remote.
        """
        self.git_session.fetch("--all")
        try:
            self.git_session.switch(self.branch)
        except GitCommandError as e:
            if f"invalid reference: {self.branch}" in str(e):
                if self.debug:
                    self.logger.info(f"Can't find branch {self.branch}")
                raise GitCommandError(
                    command=f"Switch command can't find branch {self.branch}"
                ) from e
            raise GitCommandError(command=f"Other branching error: {e}") from e

    def merge_with_remote(self) -> None:
        """Merge with changes from remote.

        Raises:
            GitCommandError: Raised and handled if merge fails.
        """
        try:
            self.git_session.merge(f"origin/{self.branch}")
        except GitCommandError as e:
            if f"couldn't find remote ref {self.branch}" in str(e):
                if self.debug:
                    self.logger.info(f"Can't find branch {self.branch}")
                    raise GitCommandError(
                        command=f"Pull command can't find branch {self.branch}",
                    ) from e
            if "exit code(128)" in str(e):
                self.clean_unmerged_files_from_local()
            if "exit code(1)" in str(e):
                self.sync_head_with_remote()
            self.sync_head_with_remote()
            raise GitCommandError(command=f"Git error: {e}") from e

    def push(self, commit_description: str, batch_size: int = 500) -> None:
        """Push latest to the git repo."""
        try:
            self.split_commits_in_batches(
                commit_description=commit_description,
                batch_size=batch_size,
            )
        except GitCommandError as e:
            self.sync_head_with_remote()
            keywords: tuple[str] = ("connection", "timed out", "unreachable")
            for keyword in keywords:
                if keyword in str(e):
                    if self.debug:
                        self.logger.info("Error pushing configs to remote repository.")
                    raise GitCommandError(
                        command=f"Error pushing configs to remote repository: {str(e)}"
                    ) from e

            if "tip of your current branch is behind" in str(e):
                try:
                    self.merge_with_remote()
                    self.split_commits_in_batches(
                        commit_description=commit_description,
                        batch_size=batch_size,
                    )
                except GitCommandError as git_error:
                    self.sync_head_with_remote()
                    raise GitCommandError(
                        command=f"Could not push changes to remote: {git_error}"
                    ) from git_error

            if "authentication failed" in str(e):
                raise GitCommandError(
                    command="Authentication fail. Please check your credentials."
                ) from e

            if "permission denied" in str(e):
                raise GitCommandError(
                    command="Permission denied. Please check your access rights."
                ) from e

            if "pre-receive hook declined" in str(e):
                raise GitCommandError(command="Pre-received hook error.") from e

            if f"cannot lock ref 'refs/heads/{self.branch}'" in str(e):
                try:
                    self.merge_with_remote()
                    self.split_commits_in_batches(
                        commit_description=commit_description,
                        batch_size=batch_size,
                    )
                except GitCommandError as git_error:
                    self.sync_head_with_remote()
                    raise GitCommandError(
                        command="The remote repository has changed since the last time pulled."
                    ) from git_error

            raise GitCommandError(command=f"Git push error: {e}") from e


# Connection Mixin Class
class ConnectionMixin:
    """Nautobot mixin to connect to a service."""

    def configure_session(self) -> Session:
        """Configure a requests session.

        Returns:
            Session: Requests session.
        """
        session: Session = Session()
        retries = Retry(
            total=3,
            backoff_factor=10,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        session.mount(
            prefix="https://",
            adapter=HTTPAdapter(max_retries=retries),
        )
        return session

    def create_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: t.Optional[dict[str, str]] = None,
        session: t.Union[Session, None] = None,
        verify: bool = True,
        logger: t.Optional[Logger] = None,
    ) -> t.Any:
        """Create request and return response.

        Args:
            method (str): HTTP Method to use.
            url (str): URL to send request to.
            headers (dict): Headers to use in request.
            body (dict): Body of request.
            session (requests.Session): Session to use.
            verify (bool): Verify SSL certificate.
            logger (t.Optional[Logger]): The Job's logger.

        Returns:
            Dict: API Response.

        Raises:
            requests.exceptions.HTTPError:
                If the HTTP request returns an unsuccessful status code.
        """
        if not isinstance(session, Session):
            raise ValueError("Session is not an instance of requests.Session")

        if not logger:
            raise ValueError("Job.logger not passed to create_request.")

        try:
            with session as ses:
                response: Response = ses.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=body,
                    timeout=(50.0, 100.0),
                    verify=verify,
                )
                response.raise_for_status()
                json_response: dict[str, t.Any] = response.json()
                return json_response
        except JSONDecodeError:
            text_response: str = response.text
            return text_response
        except HTTPError as http_err:
            logger.error(http_err)
            return


# Regex Replace

ios_regex_replace: dict[str, str] = {}
nxos_regex_replace: dict[str, str] = {}

platform_regex_replace_mapper: dict[str, dict[str, str]] = {
    "cisco_ios": ios_regex_replace,
    "cisco_nxos": nxos_regex_replace,
}


def replace_secret(
    platform_regex_mapper: dict[str, str],
    full_config: str,
) -> str:
    """Replace secret in full multiline config string.

    Args:
        platform_regex_mapper (dict[str, str]): Platform regex mapper.
        full_config (str): ull multiline config.

    Returns:
        str: Sanitized config.
    """
    sanitized_config: str = full_config
    for pattern, replacement in platform_regex_mapper.items():
        try:
            sanitized_config: str = re.sub(
                pattern=pattern,
                repl=replacement,
                string=full_config,
                flags=re.MULTILINE,
            )
        except re.error as e:
            raise re.error(
                msg=f"Regex pattern: {pattern}, Replacement: {replacement}, error: {e}"
            ) from e
    return sanitized_config


# Regex Remove
ios_regex_remove: list[str] = []
nxos_regex_remove: list[str] = []

platform_regex_remove_mapper: dict[str, list[str]] = {
    "cisco_ios": ios_regex_remove,
    "cisco_nxos": nxos_regex_remove,
}


def remove_secret(
    regex_remove_mapper: list[str],
    full_config: str,
) -> str:
    """Remove secrets in full config multiline string.

    Args:
        regex_remove_mapper (list[str]): Platform regex mapper list.
        full_config (str): Full config multiline string.

    Returns:
        str: Sanitized full config multiline string.
    """
    for pattern in regex_remove_mapper:
        full_config = re.sub(
            pattern=pattern,
            repl="",
            string=full_config,
            flags=re.MULTILINE,
        )
    return full_config


# Job

HEADERS: dict[str, str] = {
    "Authorization": "",
}

FORWARD_NETWORKS_URL: str = get_environment_variable(
    environment_variable="FORWARD_NETWORKS_HOST",
)

FORWARD_NETWORKS_SECRET_KEY: str = get_environment_variable(
    environment_variable="FORWARD_NETWORKS_SECRET_KEY",
)

FORWARD_NETWORKS_ACCESS_KEY: str = get_environment_variable(
    environment_variable="FORWARD_NETWORKS_ACCESS_KEY",
)

GeneratorAny = t.Generator[t.Any, None, None]


def get_list_of_networks() -> list[tuple[str, str]]:
    """
    Return the list of networks names to ID mappings.

    Mappings take the form of tuple['network_id': str, 'network_name': str].
    Network name is in the UI and the ID will be used in API calls.

    Raises:
        ValueError: Raises a ValueError if the secret group is not found.

    Returns:
        list[tuple[str, str]]: Choices for the network ID and name.
    """
    encoded_authorization_str: str = base_64_encode_credentials(
        username=FORWARD_NETWORKS_ACCESS_KEY,
        password=FORWARD_NETWORKS_SECRET_KEY,
    )

    HEADERS.update(
        {
            "Authorization": encoded_authorization_str,
        }
    )

    param: str = "api/networks"
    url: str = format_base_url_with_params(
        base_url=FORWARD_NETWORKS_URL,
        parameters=param,
    )

    try:
        response: Response = request(
            method="GET",
            url=url,
            headers=HEADERS,
            timeout=(50.0, 100.0),
        )

        if not response.ok:
            raise HTTPError

    except SSLError as e:
        raise SSLError(
            f"Can't find host for url {url}, or certification is invalid: {str(e)}"
        ) from e
    except HTTPError as e:
        raise HTTPError(
            f"Can't connect to Forward Networks. Is Forward Networks unavailable? Error: {str(e)}"
        ) from e

    json_response: t.Union[dict[t.Any, t.Any], list[dict[str, str]]] = response.json()

    if isinstance(json_response, dict):
        if f"No endpoint GET /{param}" in json_response["message"]:
            raise ValueError(f"The parameter /{param} is not a valid parameter.")
        if "Unable to authenticate" in json_response["message"]:
            raise ValueError("The base64 encoded credentials are incorrect.")
        raise ValueError(f"Unable to connect to Forward Networks: {json_response}")

    list_of_networks: list[tuple[str, str]] = [
        (
            network.get("id", ""),
            network.get("name", "").upper(),
        )
        for network in json_response
        if network.get("id") and network.get("name")
    ]

    return list_of_networks


name: str = "Golden Configuration"

NETWORK_CHOICES: list[tuple[str, str]] = get_list_of_networks()


class NautobotUtility:
    """Nautobot Utility Class."""

    def __init__(
        self,
        logger: Logger,
        platforms: t.Iterable[Platform],
        device_types: t.Iterable[DeviceType],
        devices: t.Iterable[Device],
        regions: t.Iterable[Location],
        sites: t.Iterable[Location],
        tags: t.Iterable[Tag],
        status: t.Iterable[Status],
    ) -> None:
        """Initialize Nautobot utility class."""
        self.logger: Logger = logger
        self.platforms: t.Iterable[Platform] = platforms
        self.device_types: t.Iterable[DeviceType] = device_types
        self.devices: t.Iterable[Device] = devices
        self.regions: t.Iterable[Location] = regions
        self.sites: t.Iterable[Location] = sites
        self.tags: t.Iterable[Tag] = tags
        self.status: t.Iterable[Status] = status
        self.filtered_devices: set[Device]
        self.valid_devices_names: set[str]

    def get_filtered_devices(self) -> None:
        """Get network devices by the passed Platform(s) from Nautobot."""
        all_q: list[Q] = []
        all_q.append(Q(platform__id__in=self.platforms))

        if self.device_types:
            all_q.append(Q(device_type__id__in=self.device_types))

        if self.devices:
            all_q.append(Q(id__in=self.devices))

        sites_q: list[Q] = []
        if self.regions:
            for region in self.regions:
                if region.descendants:
                    sites_q.append(
                        Q(location__in=region.descendants(include_self=True))
                    )

        if self.sites:
            for site in self.sites:
                sites_q.append(Q(location_id=site.id))

        if sites_q:
            combined_sites_q: Q = sites_q[0]
            if len(sites_q) >= 2:
                for q in sites_q[1:]:
                    combined_sites_q |= q
            all_q.append(combined_sites_q)

        if self.tags:
            all_q.append(Q(tags__id__in=self.tags))

        if self.status:
            all_q.append(Q(status__id__in=self.status))

        combined_q: Q = all_q[0]
        if len(all_q) >= 2:
            for q in all_q[1:]:
                combined_q &= q

        self.filtered_devices = set(Device.objects.filter(combined_q))

        if not self.filtered_devices:
            raise ValueError("No devices matches the selected filter(s).")

        self.logger.info("Grabbed all devices with the selected platforms.")

    def get_valid_filtered_devices(self) -> None:
        """Get all network devices from Nautobot."""
        self.valid_devices_names = set(
            item.name.lower() for item in self.filtered_devices if item.name
        )


class ForwardNetworksUtility(ConnectionMixin):
    """Forward Networks Utility Class."""

    def __init__(
        self,
        network_id: str,
        logger: Logger,
        debug: bool,
    ) -> None:
        """Initialize Forward Networks utility class.

        Args:
            network_id (str): FW Networks network id.
            logger (Logger): Logger object.
            debug (bool): Debug mode.
        """
        self.network_id: str = network_id
        self.logger: Logger = logger
        self.debug: bool = debug
        self.session: Session = self.configure_session()
        self.nb_device_names: set[str]
        self.nb_device_objs: set[Device]
        self.fw_networks_snapshot_id: str
        self.fw_devices: set[str]
        self.fw_device_case_mapper: dict[str, str]
        self.device_config_mapper: list[dict[str, str | Device]] = []

    def setup(
        self,
        nb_device_names: set[str],
        nb_device_objs: set[Device],
    ) -> None:
        """Setup FW Networks utility class.

        Args:
            nb_device_names (set[str]): Set of device names.
            nb_device_objs (set[Device]): Set of device objects.
        """
        self.nb_device_names = nb_device_names
        self.nb_device_objs = nb_device_objs

    def get_snapshot_id(self) -> None:
        """Get forward network snapshot id.

        Raises:
            ValueError: If snapshot id is not found.
        """
        params: str = f"/api/networks/{self.network_id}/snapshots/latestProcessed"

        url: str = format_base_url_with_params(
            base_url=FORWARD_NETWORKS_URL,
            parameters=params,
        )
        snapshot: dict[str, t.Any] = self.create_request(
            method="GET",
            url=url,
            headers=HEADERS,
            session=self.session,
            logger=self.logger,
        )

        if not snapshot:
            raise ValueError("Failed to get latest snapshot id")

        self.fw_networks_snapshot_id: str = snapshot["id"]
        self.logger.info(f"Got snapshot ID [{self.fw_networks_snapshot_id}].")

    def get_all_devices(self) -> None:
        """Get all devices from Forward Networks."""
        params: str = f"/api/networks/{self.network_id}/devices"
        url: str = format_base_url_with_params(
            base_url=FORWARD_NETWORKS_URL,
            parameters=params,
        )

        all_devices: list[dict[str, str]] = self.create_request(
            method="GET",
            url=url,
            headers=HEADERS,
            session=self.session,
            logger=self.logger,
        )

        if not all_devices:
            raise ValueError("There are no devices in this Forward Network network.")

        return all_devices

    def filtered_devices(self) -> None:
        """Get interesting devices from Forward."""
        all_devices = self.get_all_devices()
        self.fw_devices: set[str] = set(
            device["name"]
            for device in all_devices
            if device.get("name") and device.get("name").lower() in self.nb_device_names
        )

        if not self.fw_devices:
            raise ValueError(
                f"No devices in Forward Network network ID [{self.network_id}] "
                "with a device matching the filtered Nautobot devices."
            )

        self.logger.info("Grabbed all devices from Forward Networks.")

    def nb_fw_common_devices(self) -> tuple[set[Device], set[str]]:
        """Get common devices between Nautobot and Forward Networks."""
        self.fw_device_case_mapper: dict[str, str] = {
            item.lower(): item for item in self.fw_devices
        }

        fw_net_nb_common_devices: set[Device] = set()

        for selected_device in self.nb_device_objs:
            if selected_device.name.lower() in list(self.fw_device_case_mapper.keys()):
                fw_net_nb_common_devices.add(selected_device)

        if not fw_net_nb_common_devices:
            raise ValueError(
                "There are no common devices between the Nautobot filtered devices and Forward Networks."
            )

        devices_not_in_forward_networks: set[str] = set(
            item
            for item in self.nb_device_names
            if item not in list(self.fw_device_case_mapper.keys())
        )

        self.logger.info(
            "Grabbed all common devices between Nautobot and Forward Networks."
        )

        return fw_net_nb_common_devices, devices_not_in_forward_networks

    def get_device_configs(self) -> None:
        """Get device configs from forward networks."""
        (
            fw_net_nb_common_devices,
            devices_not_in_forward_networks,
        ) = self.nb_fw_common_devices()

        for fw_net_device in fw_net_nb_common_devices:
            if fw_net_device is None:
                continue

            fw_net_device_name: str = self.fw_device_case_mapper.get(
                fw_net_device.name.lower(), ""
            )

            params: str = (
                f"api/snapshots/"
                f"{self.fw_networks_snapshot_id}/devices/"
                f"{fw_net_device_name}/files/configuration.txt"
            )

            url: str = format_base_url_with_params(
                base_url=FORWARD_NETWORKS_URL,
                parameters=params,
            )

            device_files: str = self.create_request(
                method="GET",
                url=url,
                headers=HEADERS,
                session=self.session,
                logger=self.logger,
            )

            if isinstance(device_files, str):
                self.device_config_mapper.append(
                    {
                        "config": device_files,
                        "device": fw_net_device,
                    }
                )

        if not self.device_config_mapper:
            raise ValueError(
                "There were no device configurations files collected from Forward Networks."
            )

        self.logger.info("Got config for devices in the selected scope.")
        self.logger.success(f"Total backed up devices: {len(fw_net_nb_common_devices)}")

        if self.debug:
            if devices_not_in_forward_networks:
                self.logger.warning(
                    "Not all in Nautobot were found in Forward Networks."
                )
                for device in devices_not_in_forward_networks:
                    self.logger.warning(f"Device not in Forward Networks: {device}")
                self.logger.warning(
                    f"Total devices not found in Forward Networks: {len(devices_not_in_forward_networks)}"
                )


class GetConfigsFromForwardNetworks(Job):
    """Job to get configs from forward networks."""

    network_name = ChoiceVar(
        choices=NETWORK_CHOICES,
        label="Network Name",
        description="Forward Networks network name to get devices from",
        required=True,
    )

    platforms = MultiObjectVar(
        model=Platform,
        label="Platforms",
        required=True,
        description="Platforms to get configs from.",
    )

    device_types = MultiObjectVar(
        model=DeviceType,
        label="Device Types",
        required=False,
        description="Device Type to get configs from.",
    )

    devices = MultiObjectVar(
        model=Device,
        label="Devices",
        required=False,
        description="Devices to get configs from.",
    )

    regions = MultiObjectVar(
        model=Location,
        label="Regions",
        required=False,
        description="Regions to get devices from.",
    )

    sites = MultiObjectVar(
        model=Location,
        label="Sites",
        required=False,
        description="Sites to get devices from.",
        query_params={"location_type__name": "Building Location Codes"},
    )

    tag_filter = MultiObjectVar(
        model=Tag,
        label="Tags",
        required=False,
        description="Tags to filter devices on.",
    )

    status_filter = MultiObjectVar(
        model=Status,
        label="Statuses",
        required=False,
        description="Statuses to filter devices on.",
    )

    backup_repository = ObjectVar(
        model=GitRepository,
        label="Backup Repository",
        required=True,
        description="Git service repository to backup configs.",
    )

    debug = BooleanVar(
        default=False,
        label="Debug",
        description="Enable debug mode.",
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class for GetConfigsFromForwardNetworks."""

        name: str = "Get configs from Forward Networks"
        description: str = "Get configs from forward networks."

    def __init__(self, *args: t.Any, **kwargs: dict[t.Any, t.Any]) -> None:
        """Initialize GetConfigsFromForwardNetworks."""
        super().__init__(*args, **kwargs)
        self.debug: bool
        self.network_id: str
        self.platforms: t.Iterable[Platform]
        self.device_types: t.Iterable[DeviceType]
        self.devices: t.Iterable[Device]
        self.regions: t.Iterable[Location]
        self.sites: t.Iterable[Location]
        self.tags: t.Iterable[Tag]
        self.status: t.Iterable[Status]
        self.git_config: dict[str, t.Union[str, GitRepository]]

    def setup(
        self,
        debug: bool,
        network_name: str,
        platforms: t.Iterable[Platform],
        device_types: t.Iterable[DeviceType],
        devices: t.Iterable[Device],
        regions: t.Iterable[Location],
        sites: t.Iterable[Location],
        tag_filter: t.Iterable[Tag],
        status_filter: t.Iterable[Status],
        backup_repository: GitRepository,
    ) -> None:
        """Create basic setup job.

        Args:
            ... (see above class variables for detail)
        """
        self.logger.info("Setting up the job.")
        self.debug = debug
        self.network_id = network_name
        self.platforms = platforms
        self.device_types = device_types
        self.devices = devices
        self.regions = regions
        self.sites = sites
        self.tags = tag_filter
        self.status = status_filter

        if check_repository_secrets_group(repository=backup_repository):
            repo_username, repo_password = parse_credentials(
                credentials=backup_repository.secrets_group,
            )

        try:
            golden_config_setting: GoldenConfigSetting = (
                GoldenConfigSetting.objects.get(backup_repository=backup_repository)
            )
        except GoldenConfigSetting.DoesNotExist as e:
            self.logger.warning(
                "The backup repository selected is not tied to any Golden Config Setting."
            )
            raise GoldenConfigSetting.DoesNotExist(
                f"Please select a valid Golden Config Backup repository: {e}"
            ) from e

        self.logger.info("Parsed repo credentials.")
        url: str = backup_repository.remote_url
        quoted_username: str = quote(string=str(repo_username), safe="")
        quoted_token: str = quote(string=str(repo_password), safe="")
        authenticated_git_url: str = re.sub(
            pattern="//",
            repl=f"//{quoted_username}:{quoted_token}",
            string=url,
        )

        self.git_config = {
            "backup_repository_object": backup_repository,
            "backup_remote_url": authenticated_git_url,
            "backup_repository_local_path": backup_repository.filesystem_path,
            "repository_branch": backup_repository.branch,
            "repository_username": repo_username,
            "repository_password": repo_password,
            "repository_current_head": backup_repository.current_head,
            "backup_path_template": golden_config_setting.backup_path_template,
        }
        self.nb: NautobotUtility = NautobotUtility(
            logger=self.logger,
            platforms=self.platforms,
            device_types=self.device_types,
            devices=self.devices,
            regions=self.regions,
            sites=self.sites,
            tags=self.tags,
            status=self.status,
        )
        self.fw: ForwardNetworksUtility = ForwardNetworksUtility(
            network_id=self.network_id,
            logger=self.logger,
            debug=self.debug,
        )

    def atomic_get_or_create(self, model: t.Any, **kwargs: dict[t.Any, t.Any]) -> t.Any:
        """Atomic creation of objects.

        Args:
            model (t.Any): Model to get or create in Nautobot.

        Returns:
            t.Any: Created model.
        """
        retry: int = 0
        max_retries: int = 3

        while retry < max_retries:
            try:
                with transaction.atomic():
                    obj, created = model.objects.get_or_create(**kwargs)
                    return obj, created
            except OperationalError as e:
                if (
                    "Lock wait timeout exceeded; try restarting transaction"
                    in e.args[1]
                ):
                    retry += 1
                    self.logger.warning(
                        f"Encountered deadlock. Retrying {retry}/{max_retries}"
                    )
                    time.sleep(retry)
                    continue
            self.logger.warning(f"Encountered DB error: {e}")
            raise

        raise OperationalError("Max retries exceeded. Deadlock resolution failed.")

    def get_replace_patterns(self) -> bool:
        """Populate platform replace regex mappers."""
        config_replace_mapper: dict[str, dict[str, str]] = {
            "cisco_ios": ios_regex_replace,
            "cisco_nxos": nxos_regex_replace,
        }

        flag: bool = True

        for platform_name, platform_regex_dict in config_replace_mapper.items():
            self.logger.info(
                f"Loading regex replace rules for Platform {platform_name}."
            )
            try:
                platform_object = Platform.objects.get(name=platform_name)
                if platform_object is None:
                    flag = False
                    break

                replace_patterns: list[BaseManager[ConfigReplace]] = (
                    ConfigReplace.objects.filter(platform=platform_object)
                )

                if not replace_patterns.exists():
                    continue

                for rule in replace_patterns:
                    platform_regex_dict.update({rule.regex: rule.replace})
            except Platform.DoesNotExist:
                self.logger.warning(f"Platform {platform_name} does not exist.")
                continue

        return flag

    def get_remove_patterns(self) -> t.Optional[bool]:
        """Populate platform remove regex mappers."""
        config_remove_mapper: dict[str, list[str]] = {
            "cisco_ios": ios_regex_remove,
            "cisco_nxos": nxos_regex_remove,
        }

        flag: bool = True

        for platform_name, platform_regex_list in config_remove_mapper.items():
            try:
                self.logger.info(
                    f"Loading regex remove rules for Platform {platform_name}."
                )
                platform_object: Platform = Platform.objects.get(name=platform_name)
                if platform_object is None:
                    flag = False
                    break

                remove_patterns: list[BaseManager[ConfigRemove]] = (
                    ConfigRemove.objects.filter(platform=platform_object)
                )

                if not remove_patterns.exists():
                    continue

                for rule in remove_patterns:
                    platform_regex_list.append(rule.regex)
            except Platform.DoesNotExist:
                self.logger.warning(f"Platform {platform_name} does not exist.")
                continue

        return flag

    def write_backup_configs(self) -> None:
        """Write sanitized configs."""
        if not isinstance(
            self.git_config["backup_repository_object"],
            GitRepository,
        ):
            raise ValueError("Backup repository is not a GitRepository.")

        repository = GitLab(
            repository=self.git_config["backup_repository_object"],
            debug=self.debug,
            logger=self.logger,
        )

        if not isinstance(self.git_config["backup_path_template"], str):
            raise ValueError("Backup path template is not a string.")

        template = Template(source=self.git_config["backup_path_template"])
        repository.configure_local_git_repository()

        self.logger.info("Sanitizing configs and adding to local working directory.")
        backup_time: datetime = datetime.now()
        backup_time_w_timezone: datetime = backup_time.replace(
            tzinfo=pytz.timezone(zone="UTC")
        )

        for config_obj in self.fw.device_config_mapper:
            device: Device = config_obj.get("device")
            device_platform: str = device.platform.name

            try:
                rendered_string: str = template.render(obj=device)
            except UndefinedError:
                self.logger.warning(
                    f"Could not find full backup path for {device}. Skipping..."
                )
                continue

            if device_platform in platform_regex_replace_mapper.keys():
                sanitized_config: str = remove_secret(
                    regex_remove_mapper=platform_regex_remove_mapper[device_platform],
                    full_config=config_obj["config"],
                )

                sanitized_config: str = replace_secret(
                    platform_regex_mapper=platform_regex_replace_mapper[
                        device_platform
                    ],
                    full_config=sanitized_config,
                )
            else:
                sanitized_config: str = "Platform not supported."

            device_filename: str = Path(rendered_string).name
            relative_device_directory_path: str = str(Path(rendered_string).parent)

            if not isinstance(
                self.git_config["backup_repository_local_path"],
                str,
            ):
                raise ValueError("Backup repo local path is not a string.")

            full_system_device_path: Path = Path(
                self.git_config["backup_repository_local_path"]
            ).joinpath(relative_device_directory_path)

            full_system_device_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            full_system_device_file_path: Path = Path(full_system_device_path).joinpath(
                device_filename
            )

            with open(
                file=full_system_device_file_path,
                mode="w",
                encoding="utf-8",
            ) as f:
                f.write(sanitized_config.strip())

            backup_obj, created = self.atomic_get_or_create(
                model=GoldenConfig, device=device
            )

            backup_obj.backup_last_attempt_date = backup_time_w_timezone
            backup_obj.backup_last_success_date = backup_time_w_timezone
            backup_obj.backup_config = sanitized_config
            backup_obj.save()

            if created and self.debug:
                self.logger.success(
                    f"Created new GoldenConfig object with backup timestamp: {backup_obj}",
                    extra={"object": backup_obj},
                )
            elif not created and self.debug:
                self.logger.success(
                    f"Updated GoldenConfig object with backup timestamp: {backup_obj}",
                    extra={"object": backup_obj},
                )

        repository.push(
            commit_description=f"BACKUP TAKEN AT {str(backup_time)}",
            batch_size=500,
        )

    @transaction.atomic
    def run(
        self,
        network_name,
        platforms,
        device_types,
        devices,
        regions,
        sites,
        tag_filter,
        status_filter,
        backup_repository,
        debug,
    ) -> None:
        """Run job."""
        replace: bool = self.get_replace_patterns()
        if replace is False:
            self.logger.warning("There was a Platform that could not be found")
            return

        remove: bool | None = self.get_remove_patterns()
        if remove is False:
            self.logger.warning("There was a Platform that could not be found")
            return

        self.setup(
            debug=debug,
            network_name=network_name,
            platforms=platforms,
            device_types=device_types,
            devices=devices,
            regions=regions,
            sites=sites,
            tag_filter=tag_filter,
            status_filter=status_filter,
            backup_repository=backup_repository,
        )

        self.nb.get_filtered_devices()
        self.nb.get_valid_filtered_devices()
        self.fw.setup(
            nb_device_names=self.nb.valid_devices_names,
            nb_device_objs=self.nb.filtered_devices,
        )
        self.fw.get_snapshot_id()
        self.fw.filtered_devices()
        self.fw.get_device_configs()
        self.write_backup_configs()

        if self.debug:
            self.logger.success("Finished running the job!")


jobs = [GetConfigsFromForwardNetworks]

register_jobs(*jobs)
