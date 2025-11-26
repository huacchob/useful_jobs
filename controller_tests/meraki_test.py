"""nornir dispatcher for cisco Meraki."""

import pdb
from pprint import pprint

from meraki import DashboardAPI
from retrieve_secrets import get_secret

org_id, token = get_secret("meraki")

dashboard = DashboardAPI(
    api_key=token,
    base_url="https://api.meraki.com/api/v1/",
    output_log=False,
    print_console=False,
)

# resp = dashboard.organizations.updateOrganization(
#     organizationId="1278859", name="test-org"
# )
# pprint(dashboard.wireless.getNetworkWirelessSsids(networkId="N_712131691078004328"))
# print(dashboard.organizations.getOrganizations())
# print(resp.values())
# pdb.set_trace()

data = {
    "users": [],
    "access": "none",
    "communityString": "test_string",
}
print(dashboard.network.updateNetworkSnmp(networkId="N_712131691078004328", **data))
# print(dashboard.organizations.getOrganizations())
# print(resp.values())
