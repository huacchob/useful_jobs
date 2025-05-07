from base64 import b64encode
from os import environ
from pathlib import Path

from dotenv import load_dotenv

cur_dir: Path = Path(__file__).parent
load_dotenv(dotenv_path=cur_dir.joinpath("creds.env"))

# Creds
username: str = environ["USERNAME"]
password: str = environ["PASSWORD"]


def base_64_encode_credentials(username: str, password: str) -> str:
    """
    Encode username and password into base64.

    Args:
        username (str): The username to encode.
        password (str): The password to encode.

    Returns:
        str: Base64 encoded credentials.

    Raises:
        ValueError: If username or password is not a string.
    """
    credentials_str: bytes = f"{username}:{password}".encode(encoding="utf-8")
    return f"Basic {b64encode(s=credentials_str).decode(encoding='utf-8')}"


creds_encoded: str = base_64_encode_credentials(
    username=username,
    password=password,
)

print(creds_encoded)
