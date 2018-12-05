#######
## AUTHOR:  Federico G. De Faveri
## DATE:    December 2018
## PURPOSE: This program takes a list of onion web addresses and performs
##          a detailed scan for each.
## NOTES:   Thank you to automatingosint.com for the inspiration
#######


#import stem to communicate with the tor process 
from stem.control import Controller
from stem import Signal

#import dependencies
from threading import Timer
from threading import Event
import codecs
import json
import os
import random
import subprocess
import sys
import time

#initialize two empty lists that will contain onion addresses
onions = []
session_onions = []

#set Event object to coordinate later the two threads
identity_lock = Event()
identity_lock.set()

#
# grab the list of onions from our list file
#
def get_onion_list():
    
    #open the file
    if os.path.exists("onion_list.txt"):
        with open("onion_list.txt", "rb") as fd:
            stored_onions = fd.read().splitlines()
    else:
        print "[!] No onion list file 'onion_list.txt' found"
        sys.exit(1)

    print("[*] Total onions for scanning: %d" % len(stored_onions) )

    return stored_onions

#
# Stores an onion in the list of onions
#
def store_onion(onion):
    
    print("[++] Storing %s in master list." % onion)

    with codecs.open("onion_list.txt", "ab", encoding="utf8") as fd:
        fd.write("%s\n" % onion)

    return

#
# Runs onionscan as a child process
#
def run_onionstan(onion):
    
    print("[*] Onionscanning %s" % onion)

    #fire up onionscan
    process = subprocess.Popen(["onionscan", "webport=0", "--jsonreport", "--simplereport=false", onion], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #start the timer for 5 minutes
    process_timer = Timer(300, handle_timeout, args=[process, onion])
    process_timer.start()

    #wait for the onion scan results
    stdout = process.communicate()[0]

    #if the results are valid, kill the timer
    if process_timer.is_alive():
        process_timer.cancel()
        return stdout

    print("[!!] Process timed out!")

    return None

#
# Handles timer timeout from the onionscan proces
#
def hadle_timeout(process, onion):
    global session_onions
    global identity_lock
    
    #halt the main thread while we grab a new identity
    identity_lock.clear()
    
    #kill onionscan process
    try:
        process.kill()
        print("[!!] Killed the onionscan process.")
    except:
        pass

    #switch Tor identities to guarantee that we have good connection
    with Controller.from_port(port=9051) as torcontrol:

        #auth
        torcontrol.authenticate(os.environ("ONIONRUNNER_PW") )

        #send the signal for a new identity
        torcontrol.signal(Signal.NEWNYM)

        #wait for initialization of new identity
        time.sleep(torcontrol.get_newnym_wait() )

        print("[!!] Switched Tor identities")

    #push the onion back to the list
    session_onions.append(onion)
    random.shuffle(session_onions)

    #allow the main thread to resum executing
    identity_lock.set()

    return



#
# MAIN
#

print("Hello welcome " + os.environ('ONIONRUNNER_PW') )

get_onion_list()





