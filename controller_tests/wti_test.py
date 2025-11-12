import json
from base64 import b64encode
from os import environ
from pathlib import Path

from requests import request
import urllib3
from dotenv import load_dotenv
from retrieve_secrets import get_secret

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cur_dir: Path = Path(__file__).parent


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


data_put: dict[str, str] = {"unitid": {
        "hostname": "02B-WTI-OOB-LAB1",
        "siteid": "02B - Memphis Test Lab, TN",
        "location": "02B_Memphis Test Lab_TN",
        "assettag": "123",
        "domain": "ipaper.com",
},}

def WTI1():
    # Address of the WTI device
    URI = "https://"
    SITE_NAME = "164.103.40.67"

    # put in the username and password to your WTI device here
    BASE_PATH = "/api/v2/config/hostname"
    username, password = get_secret("wti")
    encoded_creds = base_64_encode_credentials(
        username=username,
        password=password,
    )
    HEADER = {
        "Authorization": encoded_creds,
        "Content-Type": "application/json",
    }

    x = request(
        url=URI + SITE_NAME + BASE_PATH,
	# method="GET",
        method="PUT",
        verify=False,
        headers=HEADER,
	data=data_put
        # params="ports=eth0",
    )
    print(json.dumps(x.json(), indent=4))


def WTI2():
    # Address of the WTI device
    URI = "https://"
    SITE_NAME = "164.103.40.67"

    # put in the username and password to your WTI device here
    BASE_PATH = "/api/v2/config/telnet"
    encoded_creds = base_64_encode_credentials(
        username=environ["WTI_USERNAME"],
        password=environ["WTI_PASSWORD"],
    )

    HEADER = {
        "Authorization": encoded_creds,
        "Content-Type": "application/json",
    }

    x = request(
        url=URI + SITE_NAME + BASE_PATH,
	method="GET",
        verify=False,
        headers=HEADER,
        params="service=tacacs",
    )
    with open("aaa_resp.json", mode="w", encoding="utf-8") as file:
        json.dump(x.json(), file, indent=4)
    print(json.dumps(x.json(), indent=4))


if __name__ == "__main__":
    # get_devices()
    WTI1()
