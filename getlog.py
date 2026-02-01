#!/usr/bin/env python3

import requests
import sys
import os
import json
import time
import sys
import getpass
import argparse
from collections import defaultdict

MAX_ATTEMPTS = 3

def load_config():
    try:
        with open(config_file, "r") as fp:
            config = json.load(fp)
        return config
    except Exception as e:
        print("Error: failed to load game version")
        raise e

def prompt_credentials():
    username = input("Username: ")
    password = getpass.getpass()
    return (username, password)


def get_credentials():
    try:
        with open(credentials_file, "r") as fp:
            creds = json.load(fp)
        username = creds["username"]
        password = creds["password"]
        return (username, password)
    except:
        return prompt_credentials()

# Log in with username/passwordtoken
# Returns token
def log_in(username, password, attempts=0):
    credentials = {
        "Email": username,
        "Password": password,
        "Version": version
    }
    # print(f"https://api.teamwood.games/0.{version}/api/user/login")
    # print(credentials)
    # exit()
    r = requests.post(f"https://api.teamwood.games/0.{version}/api/user/login", json=credentials, )

    if r.status_code == 200:
        # Update the username/password if they have changed
        with open(credentials_file, "w") as fp:
            json.dump({
                "username": username,
                "password": password,
            }, fp)
    else:
        print(f"Error {r.status_code} when authenicating: {r.reason}")
        if attempts < MAX_ATTEMPTS:
            username, password = prompt_credentials()
            return log_in(username, password, attempts+1)
        else:
            sys.exit(1)

    return r.json()["Token"]

def authenticate(token_file):
    token_expired = False
    # Authenticate to the videogame
    if os.path.isfile(token_file):
        with open(token_file, "r") as fp:
            (token, date) = json.load(fp)
        # Check whether teh token is recent
        if time.time() - date <= 14400:
            auth_header = {"Authorization": f"Bearer {token}"}
            history = requests.get(f"https://api.teamwood.games/0.{version}/api/history/fetch", headers=auth_header)
            if history.status_code != 200:
                token_expired = True
        else:
            token_expired = True
    else:
        token_expired = True

    if token_expired:
        # Re-authenticate
        username, password = get_credentials()
        token = log_in(username, password)
        auth_header = {"Authorization": f"Bearer {token}"}
        with open(token_file, "w") as fp:
            json.dump((token, int(time.time())), fp)
    
    return auth_header

def initialise_dirs():
    # Set up directory structure for storing a local copy of the output
    if not os.path.isdir(f"{base_dir}/{version}"):
        os.makedirs(f"{base_dir}/{version}")
    if not os.path.isdir(games_dir):
        os.makedirs(games_dir)

def load_history(auth_header):
    #  Get the list of recent battles
    history = requests.get(f"https://api.teamwood.games/0.{version}/api/history/fetch", headers=auth_header)
    try:
        battles = history.json()["History"]
    except Exception as e:
        print(history.status_code)
        print(history.content)
        raise e

    # Download the logs for the recent battles
    for battle in battles:
        battle_id = battle["Id"]
        # Only load battles that haven't already been loaded
        if not os.path.isfile(f"{games_dir}/{battle_id}.json"):
            details = {
                "HistoryId": battle_id,
                "Version": version,
            }

            r = requests.post(f"https://api.teamwood.games/0.{version}/api/playback/history", headers=auth_header, json=details)
            with open(f"{games_dir}/{battle_id}.json", "wb") as fp:
                fp.write(r.content)
            with open(f"{games_dir}/{battle_id}.meta.json", "w") as fp:
                json.dump(battle, fp, indent=4)
            print(battle_id)

def load_stats(auth_header):
    # Get stats
    stats = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    r = requests.get(f"https://api.teamwood.games/0.{version}/api/stats/all", headers=auth_header)
    loaded_stats = json.loads(r.content.decode())
    for stat in loaded_stats["Metrics"]:
        metric = metrics[str(stat["PrimaryMetric"])]
        mode = modes[str(stat["Mode"])]
        pack = packs[str(stat["Pack"])]
        stats[metric][mode][pack].append([
            stat["SecondaryMetric"],
            stat["Turn"],
            stat["Value"],
        ])
    with open(stats_file, "w") as fp:
        # json.dump(json.loads(r.content.decode()), fp, indent=4)
        # fp.write(r.content)
        # json.dump(stats, fp, indent=4), 
        json.dump(stats, fp) 




# Set up directory structure, create variables for file names
base_dir = "saplogger"
config_file = "config.json"
credentials_file = f"{base_dir}/credentials"
token_file = f"{base_dir}/token"
config  = load_config()
version = config["version"]
metrics = config["metrics"]
modes   = config["modes"]
packs   = config["packs"]
games_dir = f"{base_dir}/{version}/games"
initialise_dirs()
stats_file = f"{base_dir}/stats.json"

# Start logic
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='getlog',
                    description='Get stats for Super Auto Pets')
    parser.add_argument('-s', '--stats', action='store_true', help='download stats, i.e. games played pet pack, pets/food bought, etc.')
    parser.add_argument('-g', '--games', action='store_true', help='download games, i.e. most recent 20 games')
    args = parser.parse_args()
    auth_header = authenticate(token_file)
    if args.games:
        load_history(auth_header)
    if args.stats:
        load_stats(auth_header)







    