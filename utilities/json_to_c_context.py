import json
from pathlib import Path
from typing import Any

import yaml


def read_json_file_to_dict(file_path):
    """Reads a JSON file and returns its contents as a list of dictionaries."""
    with Path(file_path).open(mode="r", newline="") as jsonfile:
        return json.load(fp=jsonfile)


def write_core_router_ips(
    nodes: dict[str, str],
    yaml_dict: dict[Any, Any],
) -> dict[Any, Any]:
    for node in nodes:
        if node.get("Layer") == "Core":
            if any(
                cl in node.get("Node Name")[3:]
                for cl in ["C1", "C01", "Core1"]
            ):
                yaml_dict.update({"core_switch1_ip": node.get("IP")})
            elif any(
                cl in node.get("Node Name")[3:]
                for cl in ["C2", "C02", "Core2"]
            ):
                yaml_dict.update({"core_switch2_ip": node.get("IP")})
            elif any(
                cl in node.get("Node Name")[3:]
                for cl in ["C3", "C03", "Core3"]
            ):
                yaml_dict.update({"core_switch3_ip": node.get("IP")})
            elif "Core" in node.get("Node Name")[3:]:
                yaml_dict.update({"core_switch1_ip": node.get("IP")})
            else:
                yaml_dict.update(
                    {"site_core_unknown_ip": node.get("IP")},
                )
        elif node.get("Layer") == "Router":
            if "R1" in node.get("Node Name")[3:]:
                yaml_dict.update({"site_router1_ip": node.get("IP")})
            elif "R2" in node.get("Node Name")[3:]:
                yaml_dict.update({"site_router2_ip": node.get("IP")})
            elif "R3" in node.get("Node Name")[3:]:
                yaml_dict.update({"site_router3_ip": node.get("IP")})
            else:
                yaml_dict.update(
                    {"site_router_unknown_ip": node.get("IP")},
                )


def write_snmp_metadata(
    nodes: dict[str, str],
    yaml_dict: dict[Any, Any],
) -> dict[Any, Any]:
    for node in nodes:
        pass


def write_meraki_network_ids(
    nodes: str,
    yaml_dict: dict[Any, Any],
) -> dict[Any, Any]:
    yaml_dict.update({"networkId": list(nodes.values())[0]})
    return yaml_dict


def write_json_obj_to_context(yaml_dir: Path, json_obj: dict[Any, Any]):
    """Writes a JSON dictionary to a YAML file."""
    for nodes in json_obj:
        loc_id: str = list(nodes.keys())[0][:3]
        file_exists: bool = len(list(yaml_dir.glob(f"{loc_id}*.yml"))) == 1
        if file_exists:
            existing_file = list(yaml_dir.glob(f"{loc_id}*.yml"))[0]
        else:
            existing_file = None
        yaml_file_name = existing_file or yaml_dir.joinpath(
            f"{list(nodes.keys())[0]}.yml"
        )
        with yaml_file_name.open(mode="a") as yamlfile:
            if not file_exists:
                yamlfile.write("---\n")
                yaml_dict = {
                    "_metadata": {
                        "name": f"{list(nodes.keys())[0]} Config Context Definitions",
                        "description": f"{list(nodes.keys())[0]} Definitions",
                        "is_active": True,
                        "weight": 2500,
                    },
                }
                yaml.dump(
                    data=yaml_dict,
                    stream=yamlfile,
                    default_flow_style=False,
                    sort_keys=False,
                )
            yaml_dict: dict[Any, Any] = {}
            if file_path == "Router_Core_IPs.csv":
                yamlfile.write("\n# Core and Router IPs\n")
                write_core_router_ips(
                    nodes=nodes,
                    yaml_dict=yaml_dict,
                )
            if file_path == "SNMP_metadata.csv":
                yamlfile.write("\n# SNMP contact and location\n")
                write_snmp_metadata(
                    nodes=nodes,
                    yaml_dict=yaml_dict,
                )
            if file_path == "networks.json":
                yamlfile.write("\n# Meraki Network ID\n")
                write_meraki_network_ids(
                    nodes=nodes,
                    yaml_dict=yaml_dict,
                )
            yaml.dump(
                data=yaml_dict,
                stream=yamlfile,
                default_flow_style=False,
                sort_keys=False,
            )


file_path = "networks.json"
json_obj = read_json_file_to_dict(file_path=file_path)
# context_site_dir = Path(__file__).parent.parent.parent.joinpath(
#     "ip_repos",
#     "Templates",
#     "config_contexts",
#     "sites",
# )
context_site_dir = Path(__file__).parent.joinpath("sites")
context_site_dir.mkdir(parents=True, exist_ok=True)
write_json_obj_to_context(
    yaml_dir=context_site_dir,
    json_obj=json_obj,
)
