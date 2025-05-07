import pathlib
import re
import typing as t
from collections import OrderedDict

import yaml


def is_wildcard(mask: str) -> bool:
    """
    Check if the mask is a netmask or a wildcard mask.

    Args:
        mask (str): The mask passed that will be determined to be
                    either netmask or wildcard mask.

    Returns:
        bool: True means it is a wildcard and False means it is a netmask.
    """
    mask_split: list[str] = mask.split(sep=".")
    if mask_split[0] == "255":
        return False
    return True


def find_cidr(mask: str) -> int | None:
    """
    Finds the CIDR for the given mask.

    Args:
        mask (str): Mask to be used to find the CIDR for.
            Can parse both wildcard mask and netmask.

    Returns:
        int: CIDR.
    """
    octet_binary_map: dict[int, int] = {
        0: 0,
        128: 1,
        192: 2,
        224: 3,
        240: 4,
        248: 5,
        252: 6,
        254: 7,
        255: 8,
    }

    if not mask:
        return

    wildcard: bool = is_wildcard(mask=mask)
    mask_split: list[str] = mask.split(sep=".")

    if not wildcard:
        cidr: int = 0
        for octet in mask_split:
            if int(octet) == 255:
                cidr += 8
            else:
                cidr += octet_binary_map[int(octet)]

        return cidr
    return


def convert_cidr_to_mask(cidr: str) -> str:
    """Convert a CIDR to a subnet.

    Args:
        cidr (str): CIDR values of the ACL line.

    Returns:
        str: Subnetmask string.
    """
    list_of_full_class: list[int] = [8, 16, 24, 32]

    map_of_classless_values: dict[int, int] = {
        1: 128,
        2: 192,
        3: 224,
        4: 240,
        5: 248,
        6: 252,
        7: 254,
    }

    map_of_classfull_values: dict[int, str] = {
        8: "255.0.0.0",
        16: "255.255.0.0",
        24: "255.255.255.0",
        32: "255.255.255.255",
    }

    if int(cidr) in list_of_full_class:
        return map_of_classfull_values[int(cidr)]

    else:
        for full_class in list_of_full_class:
            subnet: str = ""
            if (full_class + 7) < int(cidr):
                continue

            classless_int_value: int = int(cidr) - full_class
            classless_subnet_value: int = map_of_classless_values[classless_int_value]
            subnet_split: list[str] = map_of_classfull_values[full_class].split(
                sep=".",
            )

            if full_class == 8:
                subnet_split[1] = str(classless_subnet_value)
                subnet: str = ".".join(subnet_split)

            if full_class == 16:
                subnet_split[2] = str(classless_subnet_value)
                subnet: str = ".".join(subnet_split)

            if full_class == 24:
                subnet_split[3] = str(classless_subnet_value)
                subnet: str = ".".join(subnet_split)

            return subnet


def is_wildcard_invertable(mask: str) -> bool:
    """
    Checks if the wildcard mask can be inverted to a netmask.

    Args:
        mask (str): Wildcard mask.

    Returns:
        bool: True if the wildcard mask can be inverted to netmask.
    """
    mask_split: list[str] = mask.split(sep=".")

    count = 0
    for octet in mask_split:
        if octet != "0":
            count += 1

    if count == 1:
        return True
    return False


def invert_mask(mask: str) -> str:
    """
    Invert a wildcard mask to netmask and vice versa.

    Args:
        mask (str): Either a netmask or wildcard mask.

    Returns:
        str: Netmask if wildcard mask is passed, and
             wildcard mask if netmask is passed.
    """
    mask_split: list[str] = mask.split(sep=".")
    wildcard_octets: list[str] = []

    for octet in mask_split:
        wildcard_octet: int = 255 - int(octet)
        wildcard_octets.append(str(wildcard_octet))

    return ".".join(wildcard_octets)


def ios_parse_acl_entry(entry: str) -> dict[str, str] | None:
    """
    Formats an ACL entry into a YAML list entry.

    Args:
        entry (str): The ACL entry to pass.

    Returns:
        dict[str, str] | None: Dictionary of the parsed ACL entries or None.
    """
    acl_regex: str = (
        r"access-list\s+"
        r"\S+\s+"
        r"(?P<action>permit|deny)\s+"
        r"(?P<src>\S+)?\s*"
        r"(?P<src_mask>\S+)?\s*"
    )

    match: re.Match[str] | None = re.match(pattern=acl_regex, string=entry)

    if match:
        acl_components: dict[str, str] = match.groupdict()
        return acl_components

    return


def ios_xr_parse_acl_entry(entry: str) -> dict[str, str] | None:
    """
    Formats an ACL entry into a YAML list entry.

    Args:
        entry (str): The ACL entry to pass.

    Returns:
        dict[str, str] | None: Dictionary of the parsed ACL entries or None.
    """
    acl_regex: str = (
        r"access-list\s+"
        r"\S+\s+"
        r"(?P<action>permit|deny)\s+"
        r"(?P<src>\S+)?\s*"
        r"(?P<src_mask>\S+)?\s*"
    )

    match: re.Match[str] | None = re.match(pattern=acl_regex, string=entry)

    if match:
        acl_components: dict[str, str] = match.groupdict()
        return acl_components

    return


def eos_parse_acl_entry(entry: str) -> dict[str, str] | None:
    """
    Formats an ACL entry into a YAML list entry.

    Args:
        entry (str): The ACL entry to pass.

    Returns:
        dict[str, str] | None: Dictionary of the parsed ACL entries or None.
    """
    acl_regex: str = (
        r"(?P<action>permit|deny)\s+(?:\s+|host\s+)"
        r"(?P<src>[\d\.]+)\s*"
        r"(?P<src_cidr>/[\d]+|\s*)"
    )

    match: re.Match[str] | None = re.match(pattern=acl_regex, string=entry)

    if match:
        acl_components: dict[str, str] = match.groupdict()
        if not acl_components["src_cidr"].isnumeric():
            acl_components["src_cidr"] = ""
        else:
            cidr: str = acl_components["src_cidr"]
            acl_components["src_cidr"] = cidr
        return acl_components

    return


def asa_parse_acl_entry(entry: str) -> dict[str, str] | None:
    """
    Formats an ACL entry into a YAML list entry.

    Args:
        entry (str): The ACL entry to pass.

    Returns:
        dict[str, str] | None: Dictionary of the parsed ACL entries or None.
    """
    acl_regex: str = (
        r"access-list\s+"
        r"\S+\s+"
        r"\S+\s+"
        r"(?P<action>permit|deny)\s+"
        r"(?P<src>\S+)?\s*"
        r"(?P<src_mask>\S+)?\s*"
    )

    match: re.Match[str] | None = re.match(pattern=acl_regex, string=entry)

    if match:
        acl_components: dict[str, str] = match.groupdict()
        return acl_components

    return


def reorder_dictionary_keys(
    dictionary: dict[t.Any, t.Any],
    order: list[t.Any],
) -> dict[str, str]:
    """
    Reorder dictionary keys.

    The list will contain the dictionary keys you want ordered going from left to right.

    Args:
        dictionary (dict[t.Any, t.Any]): Dictionary to reorder keys.
        order (list[t.Any]): List of the dictionary keys.

    Returns:
        dict[str, str]: Dictionary with the keys reordered.
    """
    ordered_dict: OrderedDict[str, str] = OrderedDict()
    for key in order:
        if key in dictionary:
            ordered_dict[key] = dictionary[key]
    return dict(ordered_dict)


def clean_acl_dictionary(
    parsed_acl: dict[str, str],
    platform: str,
) -> dict[str, str]:
    """Clean the parsed acl dictionary.

    Args:
        parsed_acl (dict[str, str]): Dictionary of regex parsed acl.
        platform (str): Platform to clean ACLs for.

    Returns:
        dict[str, str]: Clean ACL parsed dictionary.
    """
    if parsed_acl.get("src_mask"):
        wildcard: bool = is_wildcard(mask=parsed_acl["src_mask"])
        if wildcard and is_wildcard_invertable(mask=parsed_acl["src_mask"]):
            parsed_acl.update(
                {
                    "src_wildcard_mask": parsed_acl["src_mask"],
                    "src_mask": invert_mask(mask=parsed_acl["src_mask"]),
                }
            )
        elif wildcard and not is_wildcard_invertable(mask=parsed_acl["src_mask"]):
            parsed_acl.update(
                {"src_wildcard_mask": parsed_acl["src_mask"], "src_mask": ""}
            )
        else:
            parsed_acl.update(
                {
                    "src_wildcard_mask": invert_mask(mask=parsed_acl["src_mask"]),
                    "src_mask": parsed_acl["src_mask"],
                }
            )

        parsed_acl.update({"src_cidr": find_cidr(mask=parsed_acl["src_mask"])})
    else:
        if platform.startswith("eos") and parsed_acl.get("src_cidr"):
            parsed_acl.update(
                {"src_mask": convert_cidr_to_mask(cidr=parsed_acl.get("src_cidr"))}
            )

        if platform.startswith("eos") and not parsed_acl.get("src_cidr"):
            parsed_acl.update({"src_mask": "255.255.255.255"})

        parsed_acl.pop("src_cidr")

    parsed_acl.update(
        {
            "protocol": "ipv4",
            "dst": "",
            "dst_mask": "",
        }
    )

    if platform == "ios":
        for key in [""]:
            if parsed_acl.get(key):
                parsed_acl.pop(key)

    if platform == "asa":
        for key in [""]:
            if parsed_acl.get(key):
                parsed_acl.pop(key)

    if platform == "eos":
        for key in [""]:
            if parsed_acl.get(key):
                parsed_acl.pop(key)

    dictionary_key_order: list[str] = [
        "action",
        "protocol",
        "src",
        "src_mask",
        "dst",
        "dst_mask",
    ]
    ordered_acl: dict[str, str] = reorder_dictionary_keys(
        dictionary=parsed_acl,
        order=dictionary_key_order,
    )

    return ordered_acl


def write_acls_to_file(
    acl_entries: str,
    file_name: str,
    acl_yaml_list_name: str,
    platform: str,
) -> None:
    list_of_acls: list[str] = []

    count: int = 10
    for acl in acl_entries.splitlines():
        acl: str = acl.strip()
        if platform == "ios":
            parsed_acl = ios_parse_acl_entry(entry=acl)
        elif platform == "asa":
            parsed_acl = asa_parse_acl_entry(entry=acl)
        elif platform == "eos":
            parsed_acl = eos_parse_acl_entry(entry=acl)
        else:
            parsed_acl = None

        if parsed_acl:
            acl_yaml: dict[str, str] = clean_acl_dictionary(
                parsed_acl=parsed_acl,
                platform=platform,
            )
            if platform in ["ios"]:
                acl_yaml["seq"] = count
            list_of_acls.append(acl_yaml)
            yaml_syntax: dict[str, list[dict[str, str]]] = {
                acl_yaml_list_name: list_of_acls
            }
            count += 10
        else:
            raise ValueError("Function parse_acl_entry returned None")

    file_dir: pathlib.Path = pathlib.Path(__file__).parent

    with open(
        file=file_dir.joinpath(file_name),
        mode="w",
        encoding="utf-8",
    ) as f:
        yaml.dump(
            data=yaml_syntax,
            stream=f,
            sort_keys=False,
            default_flow_style=False,
        )

    print("Done creating acls")


acl_string: str = """permit host 171.174.12.135
permit host 171.149.69.89"""

write_acls_to_file(
    acl_entries=acl_string,
    file_name="acl_output.yml",
    acl_yaml_list_name="11",
    platform="eos",
)
