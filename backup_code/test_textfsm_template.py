from pathlib import Path

import textfsm

# Simulated CLI output from NX-OS
cli_output = """
______________________________________________________________
                  SNMP USERS 
______________________________________________________________

User                Auth      Priv(enforce) Groups              acl_filter       
____                ____      _____________ ______              __________       

admin               md5       aes-128(no)   network-admin       
nms21Orion          no        no            network-operator    ipv4:nmsOrion    

______________________________________________________________
 NOTIFICATION TARGET USERS (configured  for sending V3 Inform) 
______________________________________________________________

User                          Auth      Priv          
____                          ____      ____  
"""

# Load the TextFSM template
file_path = Path(__file__).parent
template_path = file_path.joinpath("cisco_nxos_show_snmp_user.textfsm")
with open(template_path) as template_file:
    fsm = textfsm.TextFSM(template_file)
    parsed_results = fsm.ParseText(cli_output)

# Print parsed results in readable form
print("\nParsed SNMP Users:")
parsed_users = []
for row in parsed_results:
    parsed_users.append(dict(zip(fsm.header, row)))
print(parsed_users)
# for row in parsed_results:
#     print(dict(zip(fsm.header, row)))
