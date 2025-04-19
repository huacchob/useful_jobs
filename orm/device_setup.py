from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Device,
    DeviceType,
    Interface,
    Location,
    LocationType,
    Manufacturer,
    Platform,
)
from nautobot.extras.models import Role, Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

# Vars
status_name = "Active"
role_name = "Network"
manufacturer_name = "Citrix"
device_type_name = "Netscaler-Type"
platform_name = "netscaler"
network_driver_name = "netscaler"
region_lt_name = "Region"
country_lt_name = "Country"
state_lt_name = "State"
city_lt_name = "City"
building_lt_name = "Building"
region_name = "AMRS"
country_name = "United States"
state_name = "North Carolina"
city_name = "Charlotte"
building_name = "UNCC"
device_name = "netscaler1"
namespace_name = "Global"
prefix_range = "192.168.100.0/24"
ip_addr = "192.168.100.10/32"
interface_name = "int1"

# Contet types
device_ct = ContentType.objects.get_for_model(model=Device)
interface_ct = ContentType.objects.get_for_model(model=Interface)

# status
status, _ = Status.objects.get_or_create(name=status_name)

# Role
role, _ = Role.objects.get_or_create(
    name=role_name,
)

role.content_types.add(device_ct, interface_ct)

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
building_lt.content_types.add(device_ct)

region, _ = Location.objects.get_or_create(
    name=region_name,
    defaults={
        "location_type": region_lt,
        "status": status,
    },
)

country, _ = Location.objects.get_or_create(
    name=country_name,
    defaults={
        "location_type": country_lt,
        "status_id": status.id,
    },
)

state, _ = Location.objects.get_or_create(
    name=state_name,
    defaults={
        "location_type": state_lt,
        "status_id": status.id,
    },
)

city, _ = Location.objects.get_or_create(
    name=city_name,
    defaults={
        "location_type": city_lt,
        "status_id": status.id,
    },
)

building, _ = Location.objects.get_or_create(
    name=building_name,
    defaults={
        "location_type": building_lt,
        "status_id": status.id,
    },
)

# Manufacturer
manufacturer, _ = Manufacturer.objects.get_or_create(
    name=manufacturer_name,
)

# Device Type
dt, _ = DeviceType.objects.get_or_create(
    manufacturer_id=manufacturer.id,
    model=device_type_name,
)

# Platform
plat, _ = Platform.objects.get_or_create(
    name=platform_name,
    manufacturer_id=manufacturer.id,
    network_driver=network_driver_name,
)

# Device
device, _ = Device.objects.get_or_create(
    name=device_name,
    device_type=dt,
    role=role,
    location=building,
    status=status,
    platform=plat,
)

# Namespace
namespace, _ = Namespace.objects.get_or_create(
    name=namespace_name,
)

# Prefix
prefix, _ = Prefix.objects.get_or_create(
    prefix=prefix_range,
    namespace=namespace,
)

# IP Address
ip, _ = IPAddress.objects.get_or_create(
    address=ip_addr,
    status_id=status.id,
)

# Interface
interface, _ = Interface.objects.get_or_create(
    name=interface_name,
    device_id=device.id,
    status_id=status.id,
    role_id=role.id,
    type="virtual",
)
# interface = Interface.objects.get(
#     name=interface_name,
#     device_id=device.id,
#     status_id=status.id,
#     role_id=role.id,
#     type="virtual",
# )
