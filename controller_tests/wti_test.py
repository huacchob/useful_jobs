from base64 import b64encode
from os import environ
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cur_dir: Path = Path(__file__).parent
load_dotenv(dotenv_path=cur_dir.joinpath("creds.env"))


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


def WTI():
    # Address of the WTI device
    URI = "https://"
    SITE_NAME = "164.103.40.67"

    # put in the username and password to your WTI device here
    BASE_PATH = "/api/v2/config/snmpaccess"
    encoded_creds = base_64_encode_credentials(
        username=environ["WTI_USERNAME"],
        password=environ["WTI_PASSWORD"],
    )
    HEADER = {
        "Authorization": encoded_creds,
        "Content-Type": "application/json",
    }

    x = requests.get(
        url=URI + SITE_NAME + BASE_PATH,
        verify=False,
        headers=HEADER,
        params="ports=eth0",
    )
    print(x.text)


# def WTI2():
#     # Address of the WTI device
#     URI = "https://"
#     SITE_NAME = "164.103.40.67"

#     # put in the username and password to your WTI device here
#     BASE_PATH = "/api/v2/config/aaaserver"
#     USERNAME = "username"
#     PASSWORD = "password"
#     AUTH = (USERNAME, PASSWORD)
#     HEADER = ""

#     x = requests.get(
#         URI + SITE_NAME + BASE_PATH,
#         verify=False,
#         auth=AUTH,
#         headers=HEADER,
#         params="service=tacacs",
#     )
#     print(x.text)


if __name__ == "__main__":
    # get_devices()
    WTI()
