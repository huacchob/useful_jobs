"""nornir dispatcher for cisco Meraki."""

from os import environ
from pathlib import Path

from dotenv import load_dotenv
from meraki import DashboardAPI

cur_dir: Path = Path(__file__).parent
load_dotenv(dotenv_path=cur_dir.joinpath("creds.env"))

dashboard = DashboardAPI(
    api_key=environ["API_KEY"],
    base_url="https://api.meraki.com/api/v1/",
    output_log=False,
    print_console=False,
)

# dashboard.organizations.updateOrganization(organizationId="1278859", name="test-org")
# print(dashboard.organizations.getOrganization(organizationId="1278859"))
print(dashboard.organizations.getOrganizations())
