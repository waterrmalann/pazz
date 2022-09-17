## Imports.
import os
import sqlite3
import time
import random
import pyperclip
import string

## Hashing, Encoding, & Encryption.
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import bcrypt
from Crypto.Random import get_random_bytes, random
import base64
from gpw import generatePronouncable

# Connect to local database and retrieve cursor.
DATABASE = sqlite3.connect("data/passwordDatabase.db")
DB_CURSOR = DATABASE.cursor()

# Check if entries table is already defined.
query = DB_CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entries'")
result = query.fetchall()
if len(result) == 0:
    # If not, create the table.
    DB_CURSOR.execute("CREATE TABLE entries(id, title, profile, password, notes, timestamp, salt)")

# Check if config table is already defined.
query = DB_CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
result = query.fetchall()
if len(result) == 0:
    # If not, create the table.
    DB_CURSOR.execute("CREATE TABLE config(keyName, keyValue)")
    DB_CURSOR.execute("INSERT INTO config VALUES(?, ?)", ('masterPassword', ''))
    DATABASE.commit()

# Global Variables          
MASTER_PASS = ''
with open("data/wordlist.txt") as f:
    PASSPHRASES = [line.strip() for line in f.readlines() if line.strip()]
    
# Utility functions to hash, encrypt, and decrypt passwords.
def hash_SHA256(text):
    """Hash an input string using the SHA-256 hashing algorithm."""
    return SHA256.new(text.encode()).hexdigest()

def derive_key(password, salt):
    """Derive a fixed length key from a password string."""
    b64pwd = base64.b64encode(SHA256.new(password.encode()).digest())
    bcrypt_hash = bcrypt(b64pwd, 12, salt)
    return bcrypt_hash[:32]

def encrypt_AES(text, key):
    """Encrypt a string using the AES-256 encryption algorithm."""
    # Warning: Insecure Implementation
    cipher = AES.new(key, AES.MODE_CFB, key[::-1][:16])
    return base64.b64encode(cipher.encrypt(text.encode())).decode()

def decrypt_AES(text, key):
    """Decrypt an AES-256 encrypted string from key."""
    # Warning: Insecure Implementation
    cipher = AES.new(key, AES.MODE_CFB, key[::-1][:16])
    return cipher.decrypt(base64.b64decode(text)).decode()

# Utility functions to generate strong, secure passwords
def genpwd_RSM(length):
    """Generates random string passwords."""
    alpha = string.ascii_lowercase
    alpha_upper = string.ascii_uppercase
    digits = string.digits
    symbols = '-+_!@#$%^&*.,?]'
    
    r = divmod(length, 4)
    
    gen_string = []
    gen_string += random.sample(alpha, k=r[0])
    gen_string += random.sample(alpha_upper, k=r[0])
    gen_string += random.sample(digits, k=r[0])
    gen_string += random.sample(symbols, k=r[0])
    gen_string += random.sample(alpha + alpha_upper + digits + symbols, k=r[1]) # remainder
    random.shuffle(gen_string)
    
    return ''.join(gen_string)
    
def genpwd_PP(length):
    """Generates passphrases."""
    return ' '.join(random.sample(PASSPHRASES, k=length))
    
def genpwd_GPW(length):
    """Generates pronouncable pseudoword passwords."""
    return generatePronouncable(length)

# Utility functions to manage the terminal.
def cls():
    """Clear the console screen."""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def title(text):
    """Set the console window title."""
    if os.name == 'nt':
        os.system(f'title {text}')
    else:
        print(f'\33]0;{text}\a', end='', flush=True)
    
def pause(message):
    """Pause the console window and await keyboard input."""
    print(message)
    if os.name == 'nt':
        os.system('pause>nul')
    else:
        os.system(f'read -p "{message}"') # untested

def print_header():
    """Print a large fancy heading text."""
    print()
    print(r"  ██████╗  █████╗ ███████╗███████╗")
    print(r"  ██╔══██╗██╔══██╗╚══███╔╝╚══███╔╝")
    print(r"  ██████╔╝███████║  ███╔╝   ███╔╝ ")
    print(r"  ██╔═══╝ ██╔══██║ ███╔╝   ███╔╝  ")
    print(r"  ██║     ██║  ██║███████╗███████╗")
    print(r"  ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝")

# Utility functions
def input_twice(prompt1, prompt2, error):
    while True:
        entry1 = input(prompt1)
        entry2 = input(prompt2)
        if entry1 == entry2:
            return entry1
        else:
            print(error)

def input_required(prompt, error):
    while True:
        entry = input(prompt)
        if entry.strip():
           return entry
        else:
            print(error)

def input_integer(prompt, error, minmax=None, default=None):
    while True:
        entry = input(prompt).strip()
        if entry.isdigit():
            num = int(entry)
            if minmax is not None:
                if num >= minmax[0] and num <= minmax[1]:
                    return num
        elif not entry and default is not None:
            return default
        print(error)

def safeExit():
    DATABASE.close()
    exit()

def main():
    """Driver function to enter the application."""
    cls()
    title("Pazz ^| Authorization")
    print("=====================================================")
    print("=====================================================")
    print_header()
    print("  A password manager written in pure Python.")
    print("=====================================================")
    print("=====================================================")
    print()
    
    # Get master password from database.
    query = DB_CURSOR.execute("SELECT keyValue FROM config WHERE keyName = 'masterPassword'")
    master_password = query.fetchone()[0]
    
    # If no master password is found. Make user generate one.
    if not master_password:
        entry_password = input_twice(
            "  Create Master Password: ", 
            "  Create Master Password (Confirmation): ", 
            "{ERROR} Password Mismatch. Enter Again.\n"
        )

        master_password = hash_SHA256(entry_password)
        DB_CURSOR.execute("UPDATE config SET keyValue=? WHERE keyName='masterPassword'", (master_password, ))
        DATABASE.commit()
        print("New Master Password Set.\n")
        
    mpass = input_required("  Enter Master Password: ", "{ERROR} Input a valid password.\n")
    
    # Verify master password.
    mpass_hashed = hash_SHA256(mpass)
    if mpass_hashed != master_password:  # check against password hash
        print("Access Denied. Incorrect Master Password.")
        safeExit()  # --> kick the user out of the application
    else:
        MASTER_PASS = master_password
        menu_showMain()  # --> allow the user into the application

def menu_showMain():
    cls()
    title("Pazz ^| Main")
    print_header()
    print()
    print("  1] List Entries")
    print("  2] Add Entry")
    print("  3] Edit Entry")
    print("  4] Delete Entry")
    print("  5] Password Generator", '\n')
    print("  6] About")
    print("  7] Exit")
    print()
    while True:
        ch = input(">> ").strip().lower()
        
        if ch in {'1', 'list', 'l'}:
            return menu_showList()
        elif ch in {'2', 'add', 'a'}:
            return menu_showAdd()
        elif ch in {'3', 'edit', 'e'}:
            return menu_showEdit()
        elif ch in {'4', 'delete', 'd', 'del'}:
            return menu_showDelete()
        elif ch in {'5', 'generator', 'p', 'pwd'}:
            return menu_showGenerator()
        elif ch in {'6', 'about', 'info', 'i'}:
            return menu_showAbout()
        elif ch in {'7', 'exit', 'quit', 'q'}:
            print("Exiting...")
            return safeExit()
        else:
            print("{ERROR} Invalid Option. Try Again. [1/2/3/4/5]")
            print()
            
def menu_showList():
    cls()
    title("Pazz ^| List Entries")
    print()
    print(r"  ╦  ╦╔═╗╔╦╗")
    print(r"  ║  ║╚═╗ ║ ")
    print(r"  ╩═╝╩╚═╝ ╩ ")
    print(r"  ──────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = query.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(F"[ID #{c}] {entry[1]}")
        if entry[2]:
            print("Profile: ", entry[2])
        print("Password: ", '[Hidden]')
        if entry[4]:
            print("Notes: ", entry[4])
        print(". . . . . ")
    print()
    while True:
        print("Enter ID to copy password to clipboard.")
        print("'back' to go back.")

        inp = input(">> ").strip().lower()
        if inp == 'back':
            print()
            return menu_showMain()
        elif inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                encrypted_passwd = results[intinp][3]
                salt = base64.b64decode(results[intinp][6])
                # Decrypt the encrypted password using key from master password.
                passwd = decrypt_AES(encrypted_passwd, derive_key(MASTER_PASS, salt))
                # Copy the password to user clipboard.
                pyperclip.copy(passwd)
                print(f"Password for {results[intinp][2]} ({results[intinp][1]}) copied to clipboard.")
                print()
            
def menu_showAdd():
    cls()
    title("Pazz ^| Add Entry")
    print()
    print(r"  ╔═╗╔╦╗╔╦╗")
    print(r"  ╠═╣ ║║ ║║")
    print(r"  ╩ ╩═╩╝═╩╝")
    print(r"  ─────────")
    print()
    
    entry_title = input_required("Enter Title: ", "{ERROR} Title is mandatory.\n")
    entry_profile = input("Enter Username/Profile: ")
    entry_password = input_twice(
        "Enter Password: ",
        "Enter Password (Confirmation): ",
        "{ERROR} Password Mismatch. Enter Again.\n"
    )
    if entry_password == 'clip':
        entry_password = pyperclip.paste().strip() or entry_password
    entry_notes = input("Additional Notes: ")
    last_modified = str(time.time())
    
    salt = get_random_bytes(16)
    salt_encoded = base64.b64encode(salt).decode()
    # Encrypt the password for secure storage.
    password_encrypted = encrypt_AES(entry_password, derive_key(MASTER_PASS, salt))
    
    id = entry_title[0] + str(random.randint(100, 999))
    data = (id, entry_title, entry_profile, password_encrypted, entry_notes, last_modified, salt_encoded)
    DB_CURSOR.execute("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?)", data)
    DATABASE.commit()
    print("Successfully added entry.")

    pause("\n  << Back [press any key]")
    menu_showMain()
    
def menu_showEdit():
    cls()
    title("Pazz ^| Edit Entry")
    print()
    print(r"  ╔═╗╔╦╗╦╔╦╗")
    print(r"  ║╣  ║║║ ║ ")
    print(r"  ╚═╝═╩╝╩ ╩ ")
    print(r"  ──────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = query.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(f"[ID #{c}] {entry[1]} | {entry[2]}")
    print()
    
    while True:
        inp = input("Enter ID (to Edit): ").strip()
        if inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                entry_data = list(results[intinp])
                uid = entry_data[0]
                
                print(f"Editing Entry {intinp} [#{uid}] (Leave blank on fields you do not wish to edit.)")
                
                print("\nTitle: ", entry_data[1])
                new_title = input("Title (New): ").strip()
                
                print("\nUsername/Profile:", entry_data[2])
                new_profile = input("Username/Profile (New): ").strip()
                
                print("\nPassword:", '[hidden]')
                new_password = ''
                while True:
                    new_password = input("Password (New): ")
                    if not new_password:
                        break
                    new_passconfirm = input("Password (Confirmation): ")
                    if new_password == new_passconfirm:
                        break
                    else:
                        print("{ERROR} Password Mismatch. Enter Again.\n")
                if new_password == 'clip':
                    new_password = pyperclip.paste().strip() or new_password
                
                print("\nNotes:", entry_data[4])
                new_notes = input("Notes (New):").strip()
                
                if new_title:
                    entry_data[1] = new_title
                if new_profile:
                    entry_data[2] = new_profile
                if new_password:
                    salt = get_random_bytes(16)
                    salt_encoded = base64.b64encode(salt).decode()
                    encrypted_password = encrypt_AES(new_password, derive_key(MASTER_PASS, salt))
                    entry_data[3] = encrypted_password
                    entry_data[6] = salt_encoded
                if new_notes:
                    entry_data[4] = new_notes
                entry_data[5] = str(time.time())
                data = tuple(entry_data)
                
                DB_CURSOR.execute("DELETE FROM entries WHERE id=?", (uid, ))
                DB_CURSOR.execute("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?)", data)
                DATABASE.commit()
                
                print("Successfully edited entry.")
                break
            else:
                print("{ERROR} Invalid ID: Out of range.\n")
        else:
            break
            
    pause("\n  << Back [press any key]")
    menu_showMain()

def menu_showDelete():
    cls()
    title("Pazz ^| Delete Entry")
    print()
    print(r"  ╔╦╗╔═╗╦  ╔═╗╔╦╗╔═╗")
    print(r"   ║║║╣ ║  ║╣  ║ ║╣ ")
    print(r"  ═╩╝╚═╝╩═╝╚═╝ ╩ ╚═╝")
    print(r"  ──────────────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = query.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(f"[ID #{c}] {entry[1]} | {entry[2]}")
    print()
    
    while True:
        inp = input("Enter ID (to Delete): ").strip()
        if inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                uid = results[intinp][0]
                DB_CURSOR.execute("DELETE FROM entries WHERE id=?", (uid, ))
                DATABASE.commit()
                print("Successfully deleted entry.")
                break
            else:
                print("Invalid ID: Out of range.\n")
        else:
            break

    pause("\n  << Back [press any key]")
    menu_showMain()

def menu_showGenerator():
    cls()
    title("Pazz ^| Password Generator")
    print()
    print(r"  ╔═╗╔═╗╔═╗╔═╗╦ ╦╔═╗╦═╗╔╦╗  ╔═╗╔═╗╔╗╔╔═╗╦═╗╔═╗╔╦╗╔═╗╦═╗")
    print(r"  ╠═╝╠═╣╚═╗╚═╗║║║║ ║╠╦╝ ║║  ║ ╦║╣ ║║║║╣ ╠╦╝╠═╣ ║ ║ ║╠╦╝")
    print(r"  ╩  ╩ ╩╚═╝╚═╝╚╩╝╚═╝╩╚══╩╝  ╚═╝╚═╝╝╚╝╚═╝╩╚═╩ ╩ ╩ ╚═╝╩╚═")
    print(r"  ─────────────────────────────────────────────────────")
    print()
    
    print("  1] Random String Method")
    print("  2] XKCD (Passphrase) Method")
    print("  3] Pseudoword Method")
    print("  4] Pseudoword + Passphrase Method", '\n')
    print("  5] Back")
    print()
    while True:
        ch = input(">> ").strip().lower()
        
        if ch in {'1', 'rs', 'random'}:
            # random string method
            length_s = input_integer("Enter String Length (10 Recommended): ", "{ERROR} Input a valid integer between 4-1024.\n", (4, 1024), 10)
            
            pwd = genpwd_RSM(length_s)
            pyperclip.copy(pwd)
            print("Generated random string password has been copied to clipboard.")
            break
            
        elif ch in {'2', 'xkcd', 'passphrase', 'pp'}:
            # passphrase
            length_pp = input_integer("Enter Passphrase Length (4 Recommended): ", "{ERROR} Input a valid integer between 4-256.\n", (4, 256), 4)
            
            pwd = genpwd_PP(length_pp)
            pyperclip.copy(pwd)
            print("Generated passphrase has been copied to clipboard.")
            break
            
        elif ch in {'3', 'pseudoword', 'pswd', 'gpw', 'pw'}:
            # pseudoword
            length_pw = input_integer("Enter Pseudoword Length (8 Recommended): ", "{ERROR} Input a valid integer between 4-32.\n", (4, 32), 8)
            
            pwd = genpwd_GPW(length_pw)
            pyperclip.copy(pwd)
            print("Generated pseudoword password has been copied to clipboard.")
            break
            
        elif ch in {'4', 'pseudoword+passphrase', 'pswdxkcd', 'pwpp'}:
            # pseudoword + passphrase
            length_pw = input_integer("Enter Pseudoword Length (6 Recommended): ", "{ERROR} Input a valid integer between 4-32.\n", (4, 32), 6)
            length_pp = input_integer("Enter Passphrase Length (4 Recommended): ", "{ERROR} Input a valid integer between 4-256.\n", (4, 256), 4)
            
            pwd = ' '.join([genpwd_GPW(length_pw) for i in range(length_pp)])
            pyperclip.copy(pwd)
            print("Generated pseudoword passphrase has been copied to clipboard.")
            break
            
        elif ch in {'5', 'back', 'b'}:
            return menu_showMain()
        else:
            print("{ERROR} Invalid Option. Try Again. [1/2/3/4/5]\n")
    
    pause("\n << Back [press any key]")
    menu_showMain()

def menu_showAbout():
    cls()
    title("Pazz ^| About")
    print()
    print(r"  ╔═╗╔╗ ╔═╗╦ ╦╔╦╗")
    print(r"  ╠═╣╠╩╗║ ║║ ║ ║ ")
    print(r"  ╩ ╩╚═╝╚═╝╚═╝ ╩ ")
    print(r"  ───────────────")
    print()
    
    print("  Pazz | by waterrmalann")
    print("  A simple cli-based password manager written in Python using SQLite.")
    print("  Version 1.0 (2022)")
    print()
    # Count number of password entries in the database.
    query = DB_CURSOR.execute("SELECT COUNT(*) FROM entries")
    result = query.fetchone()[0]
    print("  Database Entries: ", result)
    
    pause("\n << Back [press any key]")
    menu_showMain()

# Call the main() function to enter the application.
main()
