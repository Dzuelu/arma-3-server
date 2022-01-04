#!/usr/bin/python3

# MIT License
#
# Copyright (c) 2017 Marcel de Vries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import os.path
import re
import shutil
import time

from datetime import datetime
from urllib import request

#region Configuration
STEAM_CMD = "/steamcmd/steamcmd.sh"
STEAM_USER = os.environ["STEAM_USERNAME"]
STEAM_PASS = os.environ["STEAM_PASSWORD"]

A3_SERVER_DIR = "/arma3"
A3_SERVER_ID = "233780"
A3_WORKSHOP_ID = "107410"

A3_STEAM_WORKSHOP_DIR = "{}/steamapps/workshop/content/{}".format(A3_SERVER_DIR, A3_WORKSHOP_ID)
A3_LOCAL_MODS_DIR = "{}/mods".format(A3_SERVER_DIR) # Local mod folder
A3_WORKSHOP_MODS_DIR = "{}/workshop".format(A3_SERVER_DIR) # workshop mod folder
A3_KEYS_DIR = "{}/keys".format(A3_SERVER_DIR)
WORKSHOP_MODS = {} # Loaded names and ids from workshop, WORKSHOP_MODS[mod_name] = mod_id
MODS = [] # The list of mod paths to add to launch params

WORKSHOP_ID_REGEX = re.compile(r"filedetails\/\?id=(\d+)\"", re.MULTILINE)
LAST_UPDATED_REGEX = re.compile(r"workshopAnnouncement.*?<p id=\"(\d+)\">", re.DOTALL)
MOD_NAME_REGEX = re.compile(r"workshopItemTitle\">(.*?)<\/div", re.DOTALL)
WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"
#endregion

#region Functions
def env_defined(key: str):
    return key in os.environ and len(os.environ[key]) > 0


def log(msg: str):
    print("")
    print("{{0:=<{}}}".format(len(msg)).format(""))
    print(msg)
    print("{{0:=<{}}}".format(len(msg)).format(""))


def debug(message: str):
    if env_defined('DEBUG') and os.environ['DEBUG'] == '1':
        print(message)


def call_steamcmd(params: str):
    debug('steamcmd {}'.format(params))
    os.system("{} {}".format(STEAM_CMD, params))
    print("")


def remove_old_hard_links():
    if os.path.isdir(A3_KEYS_DIR):
        shutil.rmtree(A3_KEYS_DIR)
    if os.path.isdir(A3_WORKSHOP_MODS_DIR):
        shutil.rmtree(A3_WORKSHOP_MODS_DIR)


def update_server():
    steam_cmd_params  = " +login {} {}".format(STEAM_USER, STEAM_PASS)
    steam_cmd_params += " +force_install_dir {}".format(A3_SERVER_DIR)
    steam_cmd_params += " +app_update {}".format(A3_SERVER_ID)
    if env_defined("STEAM_BRANCH"):
        steam_cmd_params += " -beta {}".format(os.environ["STEAM_BRANCH"])
    if env_defined("STEAM_BRANCH_PASSWORD"):
        steam_cmd_params += " -betapassword {}".format(os.environ["STEAM_BRANCH_PASSWORD"])
    if os.environ["VALIDATE"] == '1':
        steam_cmd_params += " validate"
    steam_cmd_params += " +quit"

    call_steamcmd(steam_cmd_params)


def copy_mod_keys(mod_directory: str):
    mod_keys_directory = os.path.join(mod_directory, "keys")
    if os.path.exists(mod_keys_directory):
        create_hard_links_for_files(mod_keys_directory, A3_KEYS_DIR, False)
    else:
        print("Missing keys:", mod_keys_directory)


def download_workshop_mod(mod_id: str):
    steam_cmd_params  = " +login {} {}".format(STEAM_USER, STEAM_PASS)
    steam_cmd_params += " +force_install_dir {}".format(A3_SERVER_DIR)
    steam_cmd_params += " +workshop_download_item {} {}".format(
        A3_WORKSHOP_ID,
        mod_id
    )
    if os.environ["VALIDATE"] == '1':
        steam_cmd_params += " validate"
    steam_cmd_params += " +quit"
    call_steamcmd(steam_cmd_params)


def lowercase_workshop_dir(path: str):
    os.system("(cd {} && find . -depth -exec rename -v 's/(.*)\/([^\/]*)/$1\/\L$2/' {{}} \;)".format(path))


def check_workshop_mod(mod_id: str):
    response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read().decode("utf-8")
    mod_name = MOD_NAME_REGEX.search(response).group(1)
    mod_last_updated = LAST_UPDATED_REGEX.search(response)
    path = "{}/{}".format(A3_STEAM_WORKSHOP_DIR, mod_id)
    WORKSHOP_MODS[mod_name] = mod_id

    if os.path.isdir(path) and mod_last_updated:
        updated_at = datetime.fromtimestamp(int(mod_last_updated.group(1)))
        created_at = datetime.fromtimestamp(os.path.getctime(path))
        if (updated_at >= created_at):
            shutil.rmtree(path)
    
    if not os.path.isdir(path):
        print("Updating \"{}\" ({})".format(mod_name, mod_id))
        download_workshop_mod(mod_id)
        lowercase_workshop_dir(path)
    else:
        print("No update required for \"{}\" ({})... SKIPPING".format(mod_name, mod_id))
    # Copy keys here so it's easier to see the mod that has missing keys
    copy_mod_keys(path)


def load_workshop_mods():
    mod_file = os.environ["WORKSHOP_MODS"]
    if (mod_file == ''):
        debug("WORKSHOP_MODS env variable not set, nothing to do.")
        return
    if (mod_file.startswith("http")):
        with open("preset.html", "wb") as f:
            f.write(request.urlopen(mod_file).read())
        mod_file = "preset.html"
    with open(mod_file) as f:
        html = f.read()
        matches = re.finditer(WORKSHOP_ID_REGEX, html)
        for _, match in enumerate(matches, start=1):
            mod_id = match.group(1)
            check_workshop_mod(mod_id)


def load_mods_from_dir(directory: str, copyKeys: bool): # Loads both local and workshop mods
    for mod_folder_name in os.listdir(directory):
        mod_folder = os.path.join(directory, mod_folder_name)
        if os.path.isdir(mod_folder):
            debug("Found mod \"{}\"".format(mod_folder_name))
            MODS.append(mod_folder.replace('{}/'.format(A3_SERVER_DIR), ''))
            if copyKeys:
                copy_mod_keys(mod_folder)


def load_mods(): # Loads both local and workshop mods
    if os.path.isdir(A3_WORKSHOP_MODS_DIR):
        debug('Loading Workshop mods:')
        load_mods_from_dir(A3_WORKSHOP_MODS_DIR, False)
    if os.path.isdir(A3_LOCAL_MODS_DIR):
        debug('Loading Local mods:')
        load_mods_from_dir(A3_LOCAL_MODS_DIR, True)


def create_hard_links_for_files(real_folder: str, link_folder: str, recursive = True):
    for real_file_name in os.listdir(real_folder):
        real_item_path = os.path.join(real_folder, real_file_name)
        link_item_path = os.path.join(link_folder, real_file_name)
        if os.path.isdir(real_item_path) and recursive:
            create_hard_links_for_files(real_item_path, link_item_path)
        if os.path.isfile(real_item_path):
            if not os.path.isdir(link_folder):
                os.makedirs(link_folder)
            if not os.path.isfile(link_item_path):
                os.link(real_item_path, link_item_path)
            else:
                 # Happend with multiple a3_aegis.bikey files, it looks like multiple mods have this key also
                 # TODO: Determine if this is ok or if something else should be done
                print("Duplicate link file! This should not happen (I think). realPath: {} -> linkPath: {}".format(real_item_path, link_item_path))


def create_mod_hardlinks():
    for mod_name, mod_id in WORKSHOP_MODS.items():
        link_path = "{}/@{}".format(A3_WORKSHOP_MODS_DIR, mod_name)
        real_path = "{}/{}".format(A3_STEAM_WORKSHOP_DIR, mod_id)

        if os.path.isdir(real_path):
            debug("Creating hard link '{}'...".format(link_path))
            create_hard_links_for_files(real_path, link_path)
        else:
            print("Mod '{}' does not exist! ({})".format(mod_name, real_path))
#endregion

log("Removing old hard links to workshop/keys")
remove_old_hard_links()

log("Updating A3 server ({})".format(A3_SERVER_ID))
update_server()

log("Loading and updating workshop mods...")
load_workshop_mods()
print("Workshop mods loaded", WORKSHOP_MODS)

log("Creating workshop hard links...")
create_mod_hardlinks()

log("Creating mod list...")
load_mods()

log("Launching Arma3-server...")
launch = "{} -limitFPS={} -world={}".format(
    os.environ["ARMA_BINARY"],
    os.environ["ARMA_LIMITFPS"],
    os.environ["ARMA_WORLD"]
)
for mod in MODS:
    launch += " -mod=\"{}\"".format(mod)
if env_defined("ARMA_CDLC"):
    for cdlc in os.environ["ARMA_CDLC"].split(";"):
        launch += " -mod={}".format(cdlc)
if env_defined("ARMA_PARAMS"):
    launch += " {}".format(os.environ["ARMA_PARAMS"])
# If needed, spot for adding headlessclients or localclients
launch += ' -config="/arma3/configs/{}" -port={} -name="{}" -profiles="/arma3/configs/profiles"'.format(
    os.environ["ARMA_CONFIG"],
    os.environ["PORT"],
    os.environ["ARMA_PROFILE"]
)
# If needed, spot for adding loading of servermods
print(launch)
os.system(launch)
