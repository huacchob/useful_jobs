import json
from pathlib import Path
from typing import Any

import jmespath


def resolve_jmespath(
    jmespath_values: dict[str, str],
    api_response: Any,
) -> dict[Any, Any] | list[dict[str, Any]]:
    """Resolve jmespath.

    Args:
        jmespath_values (dict[str, str]): Jmespath dictionary.
        api_response (Any): API response.

    Returns:
        dict[Any, Any] | list[dict[str, Any]]: Resolved jmespath data fields.
    """
    data_fields: dict[str, Any] = {}

    for key, value in jmespath_values.items():
        j_value: Any = jmespath.search(
            expression=value,
            data=api_response,
        )
        if j_value:
            data_fields.update({key: j_value})
    lengths = [len(v) for v in data_fields.values() if isinstance(v, list)]
    if lengths == [1]:
        return data_fields
    if len(lengths) != len(data_fields.values()):
        return data_fields
    if len(set(lengths)) != 1:
        return data_fields
    keys = list(data_fields.keys())
    values = zip(*data_fields.values())
    return [dict(zip(keys, v)) for v in values]


resp_file = Path(__file__).parent.joinpath("aaa_resp.json")
with open(file=resp_file, mode="r", encoding="utf-8") as f:
    api_response = json.load(f)

j_values = resolve_jmespath({"aaaserver": "aaaserver"}, api_response)
print(j_values)
