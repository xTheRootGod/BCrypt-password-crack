import sys
import threading
import bcrypt

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
    print(bcolors.WARNING + '''                _
               /`_>
              / /
              |/
          ____|    __
         |    \.-``  )
         |---``\  _.'
      .-`'---``_.'
     (__...--``        Black Hat hash Crack 
                             BCrypt
''')

logo()

#--------------------------------------------------------
hash_input = input("Hash > ")  # Example: $P$FDj9XhuS43ooqUPB4EVddWAT5lCWyA1
passl = "list.txt"  # Change it to the name of the wordlist
threads = 1

try:
    plist = open(passl).readlines()
except:
    print(bcolors.FAIL + "| Couldn't find the required list!")

#--------------------------------------------------------
def crack(password):
    hashed = bcrypt.checkpw(password.encode('utf-8'), hash_input.encode('utf-8'))
    hashedpass = str(hashed) + ":" + str(password)
    
    if hashedpass == "True:" + password:
        print(bcolors.OKGREEN + "+---------------------------------------+")
        print(bcolors.OKGREEN + "| Operation completed successfully!")
        print(bcolors.OKGREEN + "| HASH > " + " " + hash_input)
        print(bcolors.OKGREEN + "| Password >" + " " + password)
        print(bcolors.OKGREEN + "+---------------------------------------+")
        sys.exit(1)

#--------------------------------------------------------
print(bcolors.OKBLUE + "+---------------------------------------+")
print(bcolors.OKBLUE + "| Cracking, please wait...")
print(bcolors.OKBLUE + "| Loaded %s passwords!" % len(plist))
print(bcolors.OKBLUE + "+---------------------------------------+")

for password in plist:
    password = password.rstrip()
    
    for i in range(threads):
        t = threading.Thread(target=crack, args=(password,))
        t.start()
