import sys
import threading
import bcrypt
from tqdm import tqdm
import os

# Variables for the total number of attempted passwords and to check if the password has been found
total_passwords_attempted = 0
password_found = False  

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
     (__...--``    BCrypt crack 2.0 Final Release
                             By Alex N
''')

logo()

#--------------------------------------------------------
hash_input = input("Hash > ")  # Example: $P$FDj9XhuS43ooqUPB4EVddWAT5lCWyA1

# Ask the user for the path to the wordlist
passl = input("Enter the path to the wordlist: ")

# Check if the provided file exists
if not os.path.exists(passl):
    print(bcolors.FAIL + "| Couldn't find the required list!")
    sys.exit(1)

threads = 1

try:
    plist = open(passl).readlines()
except:
    print(bcolors.FAIL + "| Couldn't read the provided wordlist!")

#--------------------------------------------------------
def crack(password):
    global total_passwords_attempted
    global password_found
    
    if not password_found:  
        hashed = bcrypt.checkpw(password.encode('utf-8'), hash_input.encode('utf-8'))
        hashedpass = str(hashed) + ":" + str(password)

        if hashedpass == "True:" + password:
            print(bcolors.OKGREEN + "+---------------------------------------+")
            print(bcolors.OKGREEN + "| Operation completed successfully!")
            print(bcolors.OKGREEN + "| HASH > " + " " + hash_input)
            print(bcolors.OKGREEN + "| Password >" + " " + password)
            print(bcolors.OKGREEN + "+---------------------------------------+")
            password_found = True  
            display_password_details(password)
            sys.exit(1)

        total_passwords_attempted += 1
        tqdm.write("Progress: {:,} passwords attempted".format(total_passwords_attempted), end='\r')

    # If the password has not been found and all passwords from the list have been attempted, display an error message
    if total_passwords_attempted == len(plist):
        print(bcolors.FAIL + "Password not found. Try with another wordlist.")

#--------------------------------------------------------
def display_password_details(password):
    print(bcolors.OKBLUE + "| Password Details:")
    print(bcolors.OKBLUE + "|   Length: {}".format(len(password)))
    print(bcolors.OKBLUE + "|   Characters: {}".format(' '.join(password)))
    print(bcolors.OKBLUE + "|   ASCII Values: {}".format(' '.join(str(ord(char)) for char in password)))
    print(bcolors.OKBLUE + "|   Hashed Password: {}".format(hash_input))

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
