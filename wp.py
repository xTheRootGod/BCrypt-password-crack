#!/usr/bin/python
#--------------------------------------------------------
#~Wordpress Hash Cracker
#~By Nofawkx-Al
#~Hacking Is illegal ! 
#~We love Defacement
#--------------------------------------------------------
from passlib.hash import phpass
import time
import sys
import threading
#--------------------------------------------------------
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
#--------------------------------------------------------
def logo():
    print bcolors.WARNING+ '''                _
               /`_>
              / /
              |/
          ____|    __
         |    \.-``  )
         |---``\  _.'
      .-`'---``_.'
     (__...--``        Black Hat hash Crack 
                             Nofawkx-Al
'''
logo()
#--------------------------------------------------------
hash =  raw_input("Hash > ") #~exemple : $P$FDj9XhuS43ooqUPB4EVddWAT5lCWyA1
passl = "list.txt" #~change it by wordlist name
threads = 1
try:
    plist = open(passl).readlines()
except:
    print bcolors.FAIL + "| We cant find 1 required list !"
#--------------------------------------------------------
def crack(password):
    hashed = phpass.verify(password, hash)
    hashedpass = str(hashed) + ":" + str(password)
    if hashedpass == "True:" + password :
            print bcolors.OKGREEN + "+---------------------------------------+"
            print bcolors.OKGREEN + "| Operation Completed !"
            print bcolors.OKGREEN + "| HASH > " + " " + hash
            print bcolors.OKGREEN + "| password >" + " " + password
            print bcolors.OKGREEN + "+---------------------------------------+"
            sys.exit(1)
#--------------------------------------------------------
print bcolors.OKBLUE + "+---------------------------------------+"
print bcolors.OKBLUE + "| Cracking Please Wait ..."
print bcolors.OKBLUE + "| Loaded %s passwords !" % len(plist) 
print bcolors.OKBLUE + "+---------------------------------------+"
for password in plist :
    password = password.rstrip()
    for i in xrange(threads):
        t = threading.Thread(target=crack(password))
        t.start()
#--------------------------------------------------------
