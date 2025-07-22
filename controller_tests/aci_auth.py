import json
import pdb
from typing import Any, Optional, Union

from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import JSONDecodeError
from urllib3.util import Retry


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


class NetmikoCiscoVmanage(ConnectionMixin):
    """Vmanage Controller Dispatcher class."""

    def __init__(self):
        self.session: Session = self.configure_session()
        self.get_headers: dict[str, str] = {}
        self.post_headers: dict[str, str] = {}

    def authenticate(self) -> Any:
        """Authenticate to controller.

        Args:
            logger (Logger): Logger object.
            obj (Device): Device object.
            task (Task): Nornir Task object.

        Raises:
            ValueError: Could not find the controller API URL in config context.

        Returns:
            Any: Controller object.
        """
        controller_url: str = "https://sandboxapicdc.cisco.com/"
        username, password = "admin", "!v3G@!4@Y"
        j_security_headers = {
            "Content-Type": "text/plain",
        }
        j_security_payload = {
            "aaaUser": {"attributes": {"name": f"{username}", "pwd": f"{password}"}}
        }
        # TODO: Change verify to true
        security_resp: Response = self.return_response_obj(
            session=self.session,
            method="POST",
            url=f"{controller_url}api/aaaLogin.json",
            headers=j_security_headers,
            body=json.dumps(j_security_payload),
            verify=False,
        )
        return security_resp
        # j_session_id: str = security_resp.headers.get("Set-Cookie", "")
        # if not j_session_id:
        #     raise ValueError(
        #         "Could not find getJSESSIONID from vManage controller",
        #     )
        # token_headers = {
        #     "Cookie": j_session_id,
        #     "Content-Type": "application/json",
        # }
        # # TODO: Need to make a method to determine if there is a trailing forward slash in the URL
        # token_resp: str = self.return_response_content(
        #     session=self.session,
        #     method="GET",
        #     url=f"{controller_url}dataservice/client/token",
        #     headers=token_headers,
        #     verify=False,
        # )
        # self.get_headers.update(
        #     {
        #         "Cookie": j_session_id,
        #         "Content-Type": "application/json",
        #         "X-XSRF-TOKEN": str(token_resp),
        #     }
        # )
        # return self.get_headers


dev = NetmikoCiscoVmanage()
resp = dev.authenticate()
pdb.set_trace()
