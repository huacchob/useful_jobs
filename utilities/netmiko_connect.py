import logging
from typing import Any, Dict, Optional

from netmiko import ConnectHandler
from retrieve_secrets import get_secret


username, password = get_secret("ios")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def netmiko_connect(
    device_type: str,
    host: str,
    username: str,
    password: str,
    secret: Optional[str] = None,
    port: int = 22,
    timeout: int = 10,
    **kwargs: Any,
) -> Optional[ConnectHandler]:
    """
    Establish an SSH connection to a network device using Netmiko.

    Args:
        device_type (str): The type of device (e.g., 'cisco_ios', 'juniper', etc.).
        host (str): The IP address or hostname of the device.
        username (str): The SSH username.
        password (str): The SSH password.
        secret (Optional[str]): The enable secret for devices that require it.
        port (int): The SSH port, default is 22.
        timeout (int): Connection timeout in seconds, default is 10.
        **kwargs: Additional keyword arguments for Netmiko's ConnectHandler.

    Returns:
        Optional[ConnectHandler]: An active Netmiko connection object or None if connection fails.
    """
    device_params: Dict[str, Any] = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "timeout": timeout,
    }

    if secret:
        device_params["secret"] = secret

    # Include any additional parameters passed via kwargs
    device_params.update(kwargs)

    try:
        connection = ConnectHandler(**device_params)
        breakpoint()
        if secret:
            connection.enable()
        logger.info(f"Successfully connected to {host}")
        return connection
    except Exception as e:
        logger.error(f"An error occurred while connecting to {host}: {e}")

    return None


params: Dict[str, Any] = {
    "device_type": "cisco_ios",
    "host": "10.206.24.2",
    "username": username,
    "password": password,
    "secret": password,
    "port": 22,
    "timeout": 10,
}
connection = netmiko_connect(**params)
