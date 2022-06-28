import os
import random
import subprocess as sp
import time


# Disconnect from VPN
def vpn_disconnect(directory):
    os.system(directory + "/expresso disconnect")


# Check the current VPN connection
def current_status(directory):
    try:
        vpn_status = sp.getoutput(directory + "/expresso status")
        current_connect = vpn_status[vpn_status.index("'") + 1 : vpn_status.index("' ")]
        # country=re.findall(r'\'.*?\'',vpn_status)
    except:
        current_connect = ""

    return current_connect


# Retrieve current available list of servers from ExpressVPN and choose a random country
def vpn_list(directory):
    current_connect = current_status(directory)
    vpn_list = sp.getoutput(directory + "/expresso locations").split("\n")
    countries = []

    for vpn in vpn_list:
        if len(vpn) > 0 and vpn != current_connect and vpn[0] == "-" and vpn[-1] == ")":
            countries.append(vpn[vpn.index("-") + 2 : vpn.index("(") - 1])

    country = random.choice(countries)

    return country


# Connect to a new server
def expressvpn(directory, country):

    os.system(directory + "/expresso connect --change " + '"' + country + '"')

    time.sleep(10)
