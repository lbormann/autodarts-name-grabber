import os
from pathlib import Path
import time
import json
import platform
import argparse
import requests
import logging
from urllib.parse import quote, unquote
import re
import glob
# install python-keycloak==2.13.2
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





VERSION = '1.0.0'

AUTODART_URL = 'https://autodarts.io'
AUTODART_AUTH_URL = 'https://login.autodarts.io/'
AUTODART_AUTH_TICKET_URL = 'https://api.autodarts.io/ms/v0/ticket'
AUTODART_CLIENT_ID = 'autodarts-app'
AUTODART_REALM_NAME = 'autodarts'
AUTODART_MATCHES_URL = 'https://api.autodarts.io/gs/v0/matches'


GRAB_INTERVAL = 60
TEMPLATE_FILE_EXTENSION = '.csv'
TEMPLATE_FILE_ENCODING = 'utf-8-sig'
NAMES_BLACKLISTED = [
    'bot level 1',
    'bot level 2',
    'bot level 3',
    'bot level 4',
    'bot level 5',
    'bot level 6',
    'bot level 7',
    'bot level 8',
    'bot level 9',
    'bot level 10',
    'bot level 11'
]




def ppi(message, info_object = None, prefix = '\r\n'):
    logger.info(prefix + str(message))
    if info_object != None:
        logger.info(str(info_object))
    
def ppe(message, error_object):
    ppi(message)
    if DEBUG:
        logger.exception("\r\n" + str(error_object))


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

def read_templates():
    global files_names
    files_names = {}

    # template_files = glob.glob(os.path.join(TEMPLATES_PATH, f"de-DE-v1{TEMPLATE_FILE_EXTENSION}"))
    template_files = glob.glob(os.path.join(TEMPLATES_PATH, f"*v*[0-9]{TEMPLATE_FILE_EXTENSION}"))
    # print(template_files)

    for tf in template_files:
        with open(tf, "r", encoding=TEMPLATE_FILE_ENCODING) as read_file:
            lines = read_file.readlines()

        seen = set()
        names = []
        line_length = len(lines)
        for index, line in enumerate(lines):
            name = line.split(';')[0].strip().lower()

            if name not in seen:
                if index == (line_length - 1):
                    if not line.endswith("\n"):
                        line = f'{line}\n'

                names.append((name, line))
                seen.add(name)

        files_names[tf] = names

    # print(files_names)
        
def sanitize_name(name_raw):
    name = name_raw.lower().strip()

    if '@' in name:
        return ''

    # Sonderzeichen und Zahlen am Anfang und am Ende einer Zeile entfernen
    re1 = re.sub(r'^[\d.#_\-?´|+]+', '', name)
    if re1 != name:
        return ''

    re2 = re.sub(r'[\d.#_\-?´|+]+$', '', name)
    if re2 != name:
        return ''

    # Sonderzeichen und Zahlen, die nicht am Anfang und Ende einer Zeile stehen, behandeln
    re3 = re.sub(r'[\d#_\-?´|+]', '', name)
    if re3 != name:
        return ''

    re4 = re.sub(r'\.', ' ', name)
    if re4 != name:
        return ''

    return name

def grab():
    global accessToken
    global files_names

    receive_token_autodarts()
    response = requests.get(AUTODART_MATCHES_URL, headers={'Authorization': 'Bearer ' + accessToken})
    response.raise_for_status()

    m = json.loads(response.text)  
    # ppi(json.dumps(m, indent = 4, sort_keys = True))
    
    for match in m: 
        if 'players' in match:
            for p in match['players']:
                name = sanitize_name(p['name'])
                if name != '' and name not in NAMES_BLACKLISTED:
                    for key in files_names:
                        if name not in [t[0] for t in files_names[key]]:
                            line = f"{name};;\n"
                            files_names[key].append((name, line))
                            ppi(f"'{name}' added to '{key}'")
                    
    for template_file, entries in files_names.items():
        with open(template_file, "w", encoding=TEMPLATE_FILE_ENCODING) as output_file:
            for index, entry in enumerate(entries):
                name, line = entry

                if index != len(entries) - 1:
                    output_file.write(line)
                else:
                    output_file.write(line.rstrip('\n'))


            


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    
    ap.add_argument("-U", "--autodarts_email", required=True, help="Registered email address at " + AUTODART_URL)
    ap.add_argument("-P", "--autodarts_password", required=True, help="Registered password address at " + AUTODART_URL)
    ap.add_argument("-TP", "--templates_path", required=True, help="Absolute path to your templates")
    ap.add_argument("-DEB", "--debug", type=int, choices=range(0, 2), default=False, required=False, help="If '1', the application will output additional information")
    args = vars(ap.parse_args())

    AUTODART_USER_EMAIL = args['autodarts_email']                          
    AUTODART_USER_PASSWORD = args['autodarts_password']                     
    TEMPLATES_PATH = Path(args['templates_path'])
    DEBUG = args['debug']



    global accessToken
    accessToken = None

    global files_names
    files_names = {}



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

    iteration = 0
    while True:
        try:
            read_templates()
            grab()
            iteration += 1
            ppi(f"Grab-Iteration {iteration} finished - sleep for {GRAB_INTERVAL} seconds")
        except Exception as e:
            ppe(f"Grab-Iteration {iteration} failed: ", e)
        finally:
            time.sleep(GRAB_INTERVAL)



