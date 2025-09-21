import sys
import threading
import bcrypt
from tqdm import tqdm
import os

# Variables for the total number of attempted passwords and to check if the password has been found
total_passwords_attempted = 0
password_found = False
lock = threading.Lock()

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
    print(bcolors.WARNING + r'''                _
               /`_>
              / /
              |/
          ____|    __
         |    \.-``  )
         |---``\  _.'
      .-`'---``_.'
     (__...--``    BCrypt crack 2.0 Final Release
                             By TheRootGod
                             
                             tryhackme.com/p/TheRootGod
                             github.com/xTheRootGod
                             
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
    with open(passl, 'r', encoding='utf-8', errors='ignore') as f:
        plist = f.readlines()
except Exception as e:
    print(bcolors.FAIL + f"| Couldn't read the provided wordlist! Error: {e}")
    sys.exit(1)

#--------------------------------------------------------
def crack(password):
    global total_passwords_attempted
    global password_found
    
    if password_found:
        return
    
    try:
        hashed = bcrypt.checkpw(password.encode('utf-8'), hash_input.encode('utf-8'))
        
        if hashed:
            with lock:
                if not password_found:  # Double-check to prevent multiple threads from printing
                    password_found = True
                    print(bcolors.OKGREEN + "+---------------------------------------+")
                    print(bcolors.OKGREEN + "| Operation completed successfully!")
                    print(bcolors.OKGREEN + "| HASH > " + " " + hash_input)
                    print(bcolors.OKGREEN + "| Password >" + " " + password)
                    print(bcolors.OKGREEN + "+---------------------------------------+")
                    display_password_details(password)
                    os._exit(1)  # Force exit all threads
        
        with lock:
            total_passwords_attempted += 1
            if total_passwords_attempted % 100 == 0:  # Update progress every 100 attempts
                tqdm.write(f"Progress: {total_passwords_attempted:,} passwords attempted", end='\r')
                
    except Exception as e:
        with lock:
            print(bcolors.FAIL + f"Error processing password '{password}': {e}")

#--------------------------------------------------------
def display_password_details(password):
    print(bcolors.OKBLUE + "| Password Details:")
    print(bcolors.OKBLUE + f"|   Length: {len(password)}")
    print(bcolors.OKBLUE + f"|   Characters: {' '.join(password)}")
    print(bcolors.OKBLUE + f"|   ASCII Values: {' '.join(str(ord(char)) for char in password)}")
    print(bcolors.OKBLUE + f"|   Hashed Password: {hash_input}")

#--------------------------------------------------------
print(bcolors.OKBLUE + "+---------------------------------------+")
print(bcolors.OKBLUE + f"| Cracking, please wait...")
print(bcolors.OKBLUE + f"| Loaded {len(plist)} passwords!")
print(bcolors.OKBLUE + "+---------------------------------------+")

# Create and start threads
thread_list = []
for password in plist:
    if password_found:
        break
        
    password = password.strip()
    if not password:
        continue
        
    t = threading.Thread(target=crack, args=(password,))
    t.daemon = True
    thread_list.append(t)
    t.start()
    
    # Limit the number of concurrent threads
    while threading.active_count() > threads + 1:  # +1 for main thread
        pass

# Wait for all threads to complete
for t in thread_list:
    t.join()

# If we get here and password wasn't found
if not password_found:
    print(bcolors.FAIL + "Password not found. Try with another wordlist.")
