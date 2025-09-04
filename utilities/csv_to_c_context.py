import csv
from pathlib import Path
from typing import Any

import yaml


def read_csv_file_to_dict(file_path):
    """Reads a CSV file and returns its contents as a list of dictionaries."""
    with open(file_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]


def sort_lines_by_field_into_list(field_name: str, csv_dict: list[dict]):
    """Sorts lines of a CSV dictionary by a specified field and returns a list of sorted lines."""
    discovered_fields = []
    dict_of_fields = {}
    for node_dict in csv_dict:
        if field := node_dict.get(field_name):
            if field not in discovered_fields:
                discovered_fields.append(field)
                dict_of_fields[field] = []
            if node_dict not in dict_of_fields[field]:
                dict_of_fields[field].append(node_dict)
    return dict_of_fields


def write_csv_dict_to_context(yaml_dir: Path, dict_of_fields: dict[Any, Any]):
    """Writes a CSV dictionary to a YAML file."""
    for field, nodes in dict_of_fields.items():
        yaml_file_name = Path(yaml_dir).joinpath(f"{field}.yml")
        with open(file=yaml_file_name, mode="w") as yamlfile:
            yamlfile.write("---\n")
            router_counter = 0
            yaml_dict = {
                "_metadata": {
                    "name": f"{field} Config Context Definitions",
                    "description": f"{field} Definitions",
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
            yamlfile.write("\n# Core and Router IPs\n")
            yaml_dict = {}
            for node in nodes:
                if node.get("Layer") == "Core":
                    if any(
                        cl in node.get("Node Name")[3:] for cl in ["C1", "C01", "Core1"]
                    ):
                        yaml_dict.update({"core_switch1_ip": node.get("IP")})
                    elif any(
                        cl in node.get("Node Name")[3:] for cl in ["C2", "C02", "Core2"]
                    ):
                        yaml_dict.update({"core_switch2_ip": node.get("IP")})
                    elif any(
                        cl in node.get("Node Name")[3:] for cl in ["C3", "C03", "Core3"]
                    ):
                        yaml_dict.update({"core_switch3_ip": node.get("IP")})
                    elif "Core" in node.get("Node Name")[3:]:
                        yaml_dict.update({"core_switch1_ip": node.get("IP")})
                    else:
                        yaml_dict.update({"site_core_unknown_ip": node.get("IP")})
                elif node.get("Layer") == "Router":
                    if "R1" in node.get("Node Name")[3:]:
                        yaml_dict.update({"site_router1_ip": node.get("IP")})
                    elif "R2" in node.get("Node Name")[3:]:
                        yaml_dict.update({"site_router2_ip": node.get("IP")})
                    elif "R3" in node.get("Node Name")[3:]:
                        yaml_dict.update({"site_router3_ip": node.get("IP")})
                    else:
                        yaml_dict.update({"site_router_unknown_ip": node.get("IP")})
            yaml.dump(
                data=yaml_dict,
                stream=yamlfile,
                default_flow_style=False,
                sort_keys=False,
            )


file_path = "Router_Core_IPs.csv"
csv_dict = read_csv_file_to_dict(file_path=file_path)
sorted_sites = sort_lines_by_field_into_list(field_name="Site", csv_dict=csv_dict)
context_site_dir = Path(__file__).parent.parent.parent.joinpath(
    "ip_repos", "Templates", "config_contexts", "sites"
)
context_site_dir.mkdir(parents=True, exist_ok=True)
write_csv_dict_to_context(yaml_dir=context_site_dir, dict_of_fields=sorted_sites)
