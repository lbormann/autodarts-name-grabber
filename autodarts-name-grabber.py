import os
from pathlib import Path
import time
import json
import platform
import argparse
import requests
import logging
import glob
from datetime import datetime
import signal
from mask import mask
from keycloak import KeycloakOpenID



plat = platform.system()

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
sh.setFormatter(formatter)
logger=logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.INFO)
logger.addHandler(sh)


main_directory = os.path.dirname(os.path.realpath(__file__))



VERSION = '1.0.10'

AUTODART_URL = 'https://autodarts.io'
AUTODART_AUTH_URL = 'https://login.autodarts.io/'
AUTODART_CLIENT_ID = 'autodarts-app'
AUTODART_REALM_NAME = 'autodarts'
AUTODART_MATCHES_URL = 'https://api.autodarts.io/gs/v0/matches'

DEFAULT_GRAB_INTERVAL = 60
NAMES_BLACKLISTED_FILE = "blacklisted.txt"

TEMPLATE_FILE_EXTENSION = '.csv'
TEMPLATE_FILE_ENCODING = 'utf-8-sig'
NAMES_BLACKLISTED = []
NAMES_INVALID_CHARACTERS = [
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    '0',
    '@',
    ',',
    ':',
    ';',
    '_',
    '*',
    '#',
    '?',
    '|',
    '~',
    '\\',
    '/',
    '<',
    '>',
    '"',
    '(',
    ')',
    '[',
    ']',
    '{',
    '}',
    '`',
    '´',
    '=',
    '\'',
    '&',
    '$',
    '%',
    '§',
    '²',
    '³',
    '^',
    '!'
    # '-',
    # '.',
]






def ppi(message, info_object = None, prefix = '\r\n'):
    logger.info(prefix + str(message))
    if info_object != None:
        logger.info(str(info_object))
    
def ppe(message, error_object):
    ppi(message)
    if DEBUG:
        logger.exception("\r\n" + str(error_object))

def handle_signal(signum, frame):
    global should_terminate
    should_terminate = True

signal.signal(signal.SIGTERM, handle_signal)

def contains_emoji(s):
    emoji_ranges = [
        ('\U0001F600', '\U0001F64F'),  # Emoticons
        ('\U0001F300', '\U0001F5FF'),  # Symbols & Pictographs
        ('\U0001F680', '\U0001F6FF'),  # Transport & Map Symbols
        ('\U0001F700', '\U0001F77F'),  # Alchemical Symbols
        ('\U0001F780', '\U0001F7FF'),  # Geometric Shapes Extended
        ('\U0001F800', '\U0001F8FF'),  # Supplemental Arrows-C
        ('\U0001F900', '\U0001F9FF'),  # Supplemental Symbols and Pictographs
        ('\U0001FA00', '\U0001FA6F'),  # Chess Symbols
        ('\U0001FA70', '\U0001FAFF'),  # Symbols and Pictographs Extended-A
        ('\U00002702', '\U000027B0'),  # Dingbats
    ]

    for char in s:
        for start, end in emoji_ranges:
            if start <= char <= end:
                return True
    return False

def receive_token_autodarts():
    try:
        global accessToken

        # Configure client
        keycloak_openid = KeycloakOpenID(server_url = AUTODART_AUTH_URL,
                                            client_id = AUTODART_CLIENT_ID,
                                            realm_name = AUTODART_REALM_NAME,
                                            verify = True)
        token = keycloak_openid.token(AUTODART_USER_EMAIL, AUTODART_USER_PASSWORD)
        accessToken = token['access_token']
        # ppi(token)
    except Exception as e:
        ppe('Receive token failed', e)    

def read_blacklist():
    path_to_names_blacklisted_file = os.path.join(main_directory, NAMES_BLACKLISTED_FILE)
    if os.path.exists(path_to_names_blacklisted_file):
        with open(path_to_names_blacklisted_file, 'r') as bnf:
            names_blacklisted = list(set(line.strip() for line in bnf))
            for nbd in names_blacklisted:
                NAMES_BLACKLISTED.append(nbd)

def write_blacklist():
    path_to_names_blacklisted_file = os.path.join(main_directory, NAMES_BLACKLISTED_FILE) 
    with open(path_to_names_blacklisted_file, 'w') as bnf:
        for nbd in NAMES_BLACKLISTED:
            bnf.write(nbd + '\n')

def read_templates():
    global files_entries
    files_entries = {}

    # template_files = glob.glob(os.path.join(TEMPLATES_PATH, f"de-DE-v1{TEMPLATE_FILE_EXTENSION}"))
    template_files = glob.glob(os.path.join(TEMPLATES_PATH, f"*v*[0-9]{TEMPLATE_FILE_EXTENSION}"))
    # ppi(template_files)

    for tf in template_files:
        with open(tf, "r", encoding=TEMPLATE_FILE_ENCODING) as read_file:
            lines = read_file.readlines()

        seen = set()
        entries = []
        line_length = len(lines)
        for index, line in enumerate(lines):
            sound_file_keys = line.split(';')
            spoken = sound_file_keys[0].strip().lower()

            sound_file_keys = sound_file_keys[1:] # remove spoken
            sound_file_keys = [key for key in sound_file_keys if key not in ['', '\n']] # remove empty and new line

            if spoken not in seen:
                if index == (line_length - 1):
                    if not line.endswith("\n"):
                        line = f'{line}\n'

                entries.append((spoken, line, sound_file_keys))
                seen.add(spoken)

        files_entries[tf] = entries

    # ppi(files_entries)

def write_templates():
    global files_entries

    for template_file, entries in files_entries.items():
        with open(template_file, "w", encoding=TEMPLATE_FILE_ENCODING) as output_file:
            for index, entry in enumerate(entries):
                spoken, line, sound_file_keys  = entry

                if index != len(entries) - 1:
                    output_file.write(line)
                else:
                    output_file.write(line.rstrip('\n'))


def validate_name(name_raw):
    name = name_raw.lower().strip()

    if name in NAMES_BLACKLISTED:
        return ''

    if len(name) > 25:
        NAMES_BLACKLISTED.append(name)
        ppi(f"'{name}' has to many characters - added to 'BLACKLIST'")
        return ''

    for invalid_char in NAMES_INVALID_CHARACTERS:
        if invalid_char in name:
            NAMES_BLACKLISTED.append(name)
            ppi(f"'{name}' contains invalid character - added to 'BLACKLIST'")
            return ''
        
    if contains_emoji(name):
        NAMES_BLACKLISTED.append(name)
        ppi(f"'{name}' contains invalid emoji - added to 'BLACKLIST'")
        return ''
        
    return name

def grab_names():
    global accessToken
    global files_entries

    receive_token_autodarts()
    response = requests.get(AUTODART_MATCHES_URL, headers={'Authorization': 'Bearer ' + accessToken})
    response.raise_for_status()

    m = json.loads(response.text)  
    # ppi(json.dumps(m, indent = 4, sort_keys = True))
    
    # new_name = False
    for match in m: 
        if 'players' not in match:
            continue
        for p in match['players']:
            if 'name' not in p:
                continue
            name = validate_name(p['name'])
            if name == '':
                continue
            for file in files_entries:
                files_entries_current = files_entries[file]
                if name not in [t[0] for t in files_entries_current] and name not in [t[2] for t in files_entries_current]:
                    # new_name = True
                    line = f"{name};;\n"
                    files_entries_current.append((name, line, []))
                    ppi(f"'{name}' added to '{file}'")

    # if new_name:     
        # for template_file, entries in files_entries.items():
        #     with open(template_file, "w", encoding=TEMPLATE_FILE_ENCODING) as output_file:
        #         for index, entry in enumerate(entries):
        #             spoken, line, sound_file_keys  = entry

        #             if index != len(entries) - 1:
        #                 output_file.write(line)
        #             else:
        #                 output_file.write(line.rstrip('\n'))


            


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    
    ap.add_argument("-U", "--autodarts_email", required=True, help="Registered email address at " + AUTODART_URL)
    ap.add_argument("-P", "--autodarts_password", required=True, help="Registered password address at " + AUTODART_URL)
    ap.add_argument("-TP", "--templates_path", required=True, help="Absolute path to your templates")
    ap.add_argument("-GI", "--grab_interval", type=int, required=False, default=DEFAULT_GRAB_INTERVAL, help="Grab interval in seconds")
    ap.add_argument("-DEB", "--debug", type=int, choices=range(0, 2), default=True, required=False, help="If '1', the application will output additional information")
    args = vars(ap.parse_args())

    AUTODART_USER_EMAIL = args['autodarts_email']                          
    AUTODART_USER_PASSWORD = args['autodarts_password']                     
    TEMPLATES_PATH = Path(args['templates_path'])
    GRAB_INTERVAL = args['grab_interval']
    if GRAB_INTERVAL < 0: GRAB_INTERVAL = 1
    DEBUG = args['debug']

    if DEBUG:
        ppi('Started with following arguments:')
        data_to_mask = {
            "autodarts_email": "email", 
            "autodarts_password": "str"
        }
        masked_args = mask(args, data_to_mask)
        ppi(json.dumps(masked_args, indent=4))


    global should_terminate
    should_terminate = False

    global accessToken
    accessToken = None

    global files_entries
    files_entries = {}



    osType = plat
    osName = os.name
    osRelease = platform.release()
    ppi('\r\n', None, '')
    ppi('##########################################', None, '')
    ppi('       WELCOME TO AUTODARTS-NAME-GRABBER', None, '')
    ppi('##########################################', None, '')
    ppi('VERSION: ' + VERSION, None, '')
    ppi('RUNNING OS: ' + osType + ' | ' + osName + ' | ' + osRelease, None, '')
    ppi('\r\n', None, '')

    read_blacklist()
    read_templates()

    iteration = 0
    while True:
        try:
            if should_terminate:
                ppi(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Exit-Signal received")
                break

            iteration += 1
            grab_names()  
            ppi(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Grab-Iteration {iteration} finished - sleep for {GRAB_INTERVAL} seconds")
        except Exception as e:
            ppe(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Grab-Iteration {iteration} failed: ", e)
        finally:
            time.sleep(GRAB_INTERVAL)

    write_blacklist()
    write_templates()



