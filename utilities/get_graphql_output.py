import json
from typing import Any

from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from nautobot.core.graphql.schema_init import schema
from nautobot.dcim.models import Device
from nautobot.extras.models import GraphQLQuery

# Get the stored query text
obj: GraphQLQuery = GraphQLQuery.objects.get(name="Template enrichment")
query_text: str = obj.query
variables: dict[str, str] = {"device_id": str(Device.objects.first().id)}

# Provide a request/user for permission checks
rf = RequestFactory()
request = rf.post(path="/api/graphql/")
request.user = get_user_model().objects.get(username="CHUACCH")

# Execute via Graphene schema
result: dict[Any, Any] = schema.execute(
    query_text,
    variable_values=variables,
    context_value=request,
)

path_to_file = "/home/chuacch/useful_jobs/utilities/grapgql_output.json"

with open(file=path_to_file, mode="r", encoding="utf-8") as f:
    f.write(json.dumps(obj=result.data, indent=4))
