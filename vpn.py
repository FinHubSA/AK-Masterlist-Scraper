import random
import os
import time
import subprocess as sp
import re

# Disconnect from VPN
def vpn_disconnect(directory):
    os.system(directory + '/expresso disconnect')

# Check the current VPN connection
def current_status(directory):
    vpn_status=sp.getoutput(directory + '/expresso status')
    current_connect=vpn_status[vpn_status.index("'")+1:vpn_status.index("' ")]
    #country=re.findall(r'\'.*?\'',vpn_status)

    return current_connect


# Retrieve current available list of servers from ExpressVPN
def vpn_list(directory):
    current_connect=current_status(directory)
    vpn_list=sp.getoutput(directory + '/expresso locations').split("\n")
    countries=[]

    for vpn in vpn_list:
        if len(vpn)>0 and vpn!=current_connect and vpn[0]=="-" and vpn[-1]==")":
            countries.append(vpn[vpn.index("-")+2:vpn.index("(")-1])

    return countries

# Connect to a new server
def expressvpn(directory):

    countries=vpn_list(directory)

    os.system(directory + '/expresso connect --change ' + '"' + random.choice(countries) + '"')

    time.sleep(20)


