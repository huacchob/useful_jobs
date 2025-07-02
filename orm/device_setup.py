from typing import Any

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Controller,
    Device,
    DeviceType,
    Interface,
    Location,
    LocationType,
    Manufacturer,
    Platform,
)
from nautobot.extras.models import (
    ExternalIntegration,
    Role,
    Secret,
    SecretsGroup,
    SecretsGroupAssociation,
    Status,
)
from nautobot.ipam.models import IPAddress, Namespace, Prefix

# Status
status_name = "Active"

# LT
region_lt_name = "Region"
country_lt_name = "Country"
state_lt_name = "State"
city_lt_name = "City"
building_lt_name = "Building"

# Sites
uncc_site: dict[str, str] = {
    "region_name": "AMRS",
    "country_name": "United States",
    "state_name": "North Carolina",
    "city_name": "Charlotte",
    "building_name": "UNCC",
}
sites: list[dict[str, str]] = [uncc_site]

# External Integrations
meraki_integration: dict[str, Any] = {
    "name": "Meraki Integration",
    "remote_url": "https://api.meraki.com/api/v1/",
    "verify_ssl": False,
    "timeout": 30,
}

external_integrations: list[dict[str, str]] = [meraki_integration]

# Controllers
meraki_controller: dict[str, str] = {
    "name": "Meraki Controller",
    "location": "UNCC",
    "platform": "cisco_meraki",
    "external_integration": "Meraki Integration",
}

controllers: list[dict[str, str]] = [meraki_controller]

# Devices
netscaler_dev: dict[str, str] = {
    "manufacturer_name": "Citrix",
    "device_type_name": "Netscaler-Type",
    "platform_name": "netscaler",
    "network_driver_name": "netscaler",
    "role": "Core",
    "device_name": "netscaler1",
    "location": "UNCC",
    "namespace_name": "Global",
    "prefix_range": "172.18.0.0/16",
    "ip_addr": "172.18.0.8/32",
    "interface_name": "int1",
}
nxos_dev: dict[str, str] = {
    "manufacturer_name": "Cisco",
    "device_type_name": "Nxos-Type",
    "platform_name": "cisco_nxos",
    "network_driver_name": "cisco_nxos",
    "role": "Distribution",
    "device_name": "nxos1",
    "location": "UNCC",
    "namespace_name": "Global",
    "prefix_range": "172.20.0.0/16",
    "ip_addr": "172.20.20.2/32",
    "interface_name": "int1",
}
ios_dev: dict[str, str | None] = {
    "manufacturer_name": "Cisco",
    "device_type_name": "Ios-Type",
    "platform_name": "cisco_ios",
    "network_driver_name": "cisco_ios",
    "role": "Access",
    "device_name": "ios1",
    "location": "UNCC",
    "namespace_name": None,
    "prefix_range": None,
    "ip_addr": None,
    "interface_name": None,
}
meraki_controller_device: dict[str, str | None] = {
    "manufacturer_name": "Cisco",
    "device_type_name": "Meraki-Type",
    "platform_name": "cisco_meraki",
    "network_driver_name": "cisco_meraki",
    "role": "Network",
    "device_name": "meraki_controller1",
    "location": "UNCC",
    "namespace_name": None,
    "prefix_range": None,
    "ip_addr": None,
    "interface_name": None,
}
meraki_managed_device: dict[str, str | None] = {
    "manufacturer_name": "Cisco",
    "device_type_name": "Meraki-Type",
    "platform_name": "meraki_managed",
    "network_driver_name": "meraki_managed",
    "role": "Network",
    "device_name": "meraki_managed1",
    "location": "UNCC",
    "namespace_name": None,
    "prefix_range": None,
    "ip_addr": None,
    "interface_name": None,
}
devices: list[dict[str, str | None]] = [
    netscaler_dev,
    nxos_dev,
    ios_dev,
    meraki_controller_device,
    meraki_managed_device,
]

# Secrets
netscaler_secret: dict[str, str] = {
    "secret1": "NETSCALER_USER",
    "secret2": "NETSCALER_PASS",
    "provider": "environment-variable",
    "secrets_group_name": "NETSCALER",
    "sga_access_type": "Generic",
    "sga1_secret_type": "username",
    "sga2_secret_type": "password",
    "device": "netscaler1",
}
nxos_secret: dict[str, str] = {
    "secret1": "NXOS_USER",
    "secret2": "NXOS_PASS",
    "provider": "environment-variable",
    "secrets_group_name": "NXOS",
    "sga_access_type": "Generic",
    "sga1_secret_type": "username",
    "sga2_secret_type": "password",
    "device": "nxos1",
}
meraki_controller_secret: dict[str, str] = {
    "secret1": "NXOS_USER",
    "secret2": "MERAKI_API_KEY",
    "provider": "environment-variable",
    "secrets_group_name": "MERAKI",
    "sga_access_type": "Generic",
    "sga1_secret_type": "username",
    "sga2_secret_type": "password",
    "device": "meraki_controller1",
}
meraki_managed_secret: dict[str, str] = {
    "secret1": "NXOS_USER",
    "secret2": "MERAKI_API_KEY",
    "provider": "environment-variable",
    "secrets_group_name": "MERAKI",
    "sga_access_type": "Generic",
    "sga1_secret_type": "username",
    "sga2_secret_type": "password",
    "device": "meraki_managed1",
}
secrets: list[dict[str, str]] = [
    netscaler_secret,
    nxos_secret,
    meraki_controller_secret,
    meraki_managed_secret,
]

# Contet types
controller_ct: ContentType = ContentType.objects.get_for_model(model=Controller)
device_ct: ContentType = ContentType.objects.get_for_model(model=Device)
interface_ct: ContentType = ContentType.objects.get_for_model(model=Interface)

# status
status, _ = Status.objects.get_or_create(name=status_name)

# Location types
region_lt, _ = LocationType.objects.get_or_create(
    name=region_lt_name,
)
country_lt, _ = LocationType.objects.get_or_create(
    name=country_lt_name,
    parent_id=region_lt.id,
)
state_lt, _ = LocationType.objects.get_or_create(
    name=state_lt_name,
    parent_id=country_lt.id,
)
city_lt, _ = LocationType.objects.get_or_create(
    name=city_lt_name,
    parent_id=state_lt.id,
)
building_lt, _ = LocationType.objects.get_or_create(
    name=building_lt_name,
    parent_id=city_lt.id,
)
building_lt.content_types.add(device_ct, controller_ct)

for site in sites:
    region, _ = Location.objects.get_or_create(
        name=site.get("region_name"),
        defaults={
            "location_type": region_lt,
            "status": status,
        },
    )

    country, _ = Location.objects.get_or_create(
        name=site.get("country_name"),
        defaults={
            "location_type": country_lt,
            "status_id": status.id,
        },
    )

    state, _ = Location.objects.get_or_create(
        name=site.get("state_name"),
        defaults={
            "location_type": state_lt,
            "status_id": status.id,
        },
    )

    city, _ = Location.objects.get_or_create(
        name=site.get("city_name"),
        defaults={
            "location_type": city_lt,
            "status_id": status.id,
        },
    )

    building, _ = Location.objects.get_or_create(
        name=site.get("building_name"),
        defaults={
            "location_type": building_lt,
            "status_id": status.id,
        },
    )

for external_integration in external_integrations:
    integration, _ = ExternalIntegration.objects.get_or_create(
        name=external_integration.get("name"),
        defaults={
            "remote_url": external_integration.get("remote_url"),
            "verify_ssl": external_integration.get("verify_ssl"),
            "timeout": external_integration.get("timeout"),
        },
    )

for controller in controllers:
    cntrlr_loc: Location = Location.objects.get(name=controller.get("location"))
    cntrlr_integration: ExternalIntegration = ExternalIntegration.objects.get(
        name=controller.get("external_integration"),
    )
    cntrlr_platform: Platform = Platform.objects.get(name=controller.get("platform"))
    cntrlr, _ = Controller.objects.get_or_create(
        name=controller.get("name"),
        defaults={
            "location": cntrlr_loc,
            "external_integration": cntrlr_integration,
            "platform": cntrlr_platform,
            "status": status,
        },
    )

for dev in devices:
    # Manufacturer
    manufacturer, _ = Manufacturer.objects.get_or_create(
        name=dev.get("manufacturer_name"),
    )

    # Device Type
    dt, _ = DeviceType.objects.get_or_create(
        manufacturer_id=manufacturer.id,
        model=dev.get("device_type_name"),
    )

    # Platform
    plat, _ = Platform.objects.get_or_create(
        name=dev.get("platform_name"),
        manufacturer_id=manufacturer.id,
        network_driver=dev.get("network_driver_name"),
    )

    # role
    role, created_role = Role.objects.get_or_create(
        name=dev.get("role"),
    )

    if created_role:
        role.content_types.add(device_ct, interface_ct)

    # Device
    loc = Location.objects.get(
        name=dev.get("location"),
    )
    device, _ = Device.objects.get_or_create(
        name=dev.get("device_name"),
        device_type=dt,
        role=role,
        location=loc,
        status=status,
        platform=plat,
    )

    if dev.get("ip_addr"):
        # Namespace
        namespace, _ = Namespace.objects.get_or_create(
            name=dev.get("namespace_name"),
        )

        # Prefix
        prefix, _ = Prefix.objects.get_or_create(
            prefix=dev.get("prefix_range"),
            namespace=namespace,
            status_id=status.id,
        )

        # IP Address
        ip, _ = IPAddress.objects.get_or_create(
            address=dev.get("ip_addr"),
            status_id=status.id,
        )

        # Interface
        interface, _ = Interface.objects.get_or_create(
            name=dev.get("interface_name"),
            device_id=device.id,
            status_id=status.id,
            role_id=role.id,
            type="virtual",
        )

        interface.ip_addresses.add(ip)
        interface.validated_save()

        device.primary_ip4 = ip
        device.validated_save()

for secret in secrets:
    # Secrets
    s1, _ = Secret.objects.get_or_create(
        name=secret.get("secret1"),
        provider=secret.get("provider"),
        parameters={"variable": secret.get("secret1")},
    )
    s2, _ = Secret.objects.get_or_create(
        name=secret.get("secret2"),
        provider=secret.get("provider"),
        parameters={"variable": secret.get("secret2")},
    )

    sg, sg_created = SecretsGroup.objects.get_or_create(
        name=secret.get("secrets_group_name"),
    )

    sga1, _ = SecretsGroupAssociation.objects.get_or_create(
        secret=s1,
        access_type=secret.get("sga_access_type"),
        secret_type=secret.get("sga1_secret_type"),
        secrets_group=sg,
    )
    sga2, _ = SecretsGroupAssociation.objects.get_or_create(
        secret=s2,
        access_type=secret.get("sga_access_type"),
        secret_type=secret.get("sga2_secret_type"),
        secrets_group=sg,
    )

    sg.validated_save()

    if secret.get("device"):
        device: Device = Device.objects.get(name=secret.get("device"))
        device.secrets_group = sg

        device.validated_save()
