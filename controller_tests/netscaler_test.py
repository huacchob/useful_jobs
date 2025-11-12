from typing import Any, Optional, Union

from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import JSONDecodeError
from retrieve_secrets import get_secret
from urllib3.util import Retry

verify: bool = False
username, password = get_secret("netscaler")
hostname = "https://i02a-devtest-lb"
endpoint = f"{hostname}/nitro/v1/config/auditsyslogaction"


class ConnectionMixin:
    """Mixin to connect to a service."""

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

    def return_response_content(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        session: Session,
        body: Optional[Union[dict[str, str], str]] = None,
        verify: bool = True,
    ) -> Any:
        """Create request and return response payload.

        Args:
            method (str): HTTP Method to use.
            url (str): URL to send request to.
            headers (dict): Headers to use in request.
            session (Session): Session to use.
            body (Optional[Union[dict[str, str], str]]): Body of request.
            verify (bool): Verify SSL certificate.

        Returns:
            Any: API Response.

        Raises:
            requests.exceptions.HTTPError:
                If the HTTP request returns an unsuccessful status code.
        """
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
                json_response: dict[str, Any] = response.json()
                return json_response
        except JSONDecodeError:
            text_response: str = response.text
            return text_response

    def return_response_obj(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        session: Session,
        body: Optional[Union[dict[str, str], str]] = None,
        verify: bool = True,
    ) -> Response:
        """Create request for authentication and return response object.

        Args:
            method (str): HTTP Method to use.
            url (str): URL to send request to.
            headers (dict): Headers to use in request.
            session (Session): Session to use.
            logger (Logger): The dispatcher's logger.
            body (Optional[Union[dict[str, str], str]]): Body of request.
            verify (bool): Verify SSL certificate.

        Returns:
            Response: API Response object.
        """
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
            return response


session = ConnectionMixin().configure_session()

get_headers = {
    "X-NITRO-USER": username,
    "X-NITRO-PASS": password,
    "Content-Type": "application/json",
}

response: Any = ConnectionMixin().return_response_content(
    session=session,
    method="GET",
    url=endpoint,
    headers=get_headers,
    verify=verify,
)

print(response)
