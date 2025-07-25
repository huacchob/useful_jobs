from typing import Any

import jmespath

api_response = {
    "totalCount": "20",
    "imdata": [
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "orchestrator:terraform",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-infra",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-21T11:51:41.446+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "infra",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "0",
                    "userdom": "all",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-common",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-21T09:21:46.810+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "common",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "0",
                    "userdom": "all",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "orchestrator:terraform",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-mgmt",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-21T11:51:41.455+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "mgmt",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "0",
                    "userdom": "all",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "Try ACI tool demo at https://oneaciapp.talapupa.com",
                    "dn": "uni/tn-oneaciapp",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T01:58:12.856+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "oneaciapp",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-bmh-tenant",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T11:04:13.538+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "bmh-tenant",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-Tenant_TN",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T11:07:04.535+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "Tenant_TN",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-Osheen",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T11:39:13.086+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "Osheen",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-Automated_Tenant_02",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T11:48:29.905+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "Automated_Tenant_02",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-Amuge-Tenant",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T16:11:37.410+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "Amuge-Tenant",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-tayssirtenant",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T20:28:47.862+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "tayssirtenant",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "orchestrator:terraform",
                    "childAction": "",
                    "descr": "Terraform-created tenant",
                    "dn": "uni/tn-TF_SANDBOX_TENANT",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-22T20:36:55.656+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "TF_SANDBOX_TENANT",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "for study",
                    "dn": "uni/tn-A1",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T06:39:02.301+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "A1",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-SanXuat",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T08:12:27.193+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "SanXuat",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-MDC-TENANT",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T08:32:41.688+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "MDC-TENANT",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-TN_VINO",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T09:25:00.270+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "TN_VINO",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-web-tenanat",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T09:43:19.202+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "web-tenanat",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-TN-IAI",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T11:17:28.147+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "TN-IAI",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "orchestrator:ansible",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-jinwa-test",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T11:17:52.352+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "jinwa-test",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-Rehan123",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T11:31:41.697+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "Rehan123",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
        {
            "fvTenant": {
                "attributes": {
                    "annotation": "",
                    "childAction": "",
                    "descr": "",
                    "dn": "uni/tn-TC-Tenant",
                    "extMngdBy": "",
                    "lcOwn": "local",
                    "modTs": "2025-07-23T13:04:57.527+00:00",
                    "monPolDn": "uni/tn-common/monepg-default",
                    "name": "TC-Tenant",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": "",
                    "status": "",
                    "uid": "15374",
                    "userdom": ":all:",
                }
            }
        },
    ],
}

# jmespath_values = {
#     "name": "imdata[*].fvTenant",
#     "annotation": "imdata[*].fvTenant",
# }
jmespath_values = {
    "name": "imdata[*].fvTenant.attributes.name",
    "annotation": "imdata[*].fvTenant.attributes.annotation",
}

data_fields: dict[str, Any] = {}
for key, value in jmespath_values.items():
    j_value: Any = jmespath.search(
        expression=value,
        data=api_response,
    )
    if j_value:
        data_fields.update({key: j_value})
lengths = [len(v) for v in data_fields.values() if isinstance(v, list)]
if len(lengths) != len(data_fields.values()):
    print("return data_fields")
if len(set(lengths)) != 1:
    print("return data_fields")
keys = list(data_fields.keys())
values = zip(*data_fields.values())
result = [dict(zip(keys, v)) for v in values]

print(result)
# print(json.dumps(data_fields, indent=4))
