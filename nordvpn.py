import random
import os
import time

countries_list=['al','ar','au']

def nordvpn():
    command="nordvpn connect "+random.choice(countries_list)#+" >/dev/null 2>&1"
    print(command)
    os.system(command)
    time.sleep(10)

nordvpn()

