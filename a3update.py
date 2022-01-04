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

A3_WORKSHOP_DIR = "{}/steamapps/workshop/content/{}".format(A3_SERVER_DIR, A3_WORKSHOP_ID)
A3_MODS_DIR = "{}/mods".format(A3_SERVER_DIR)
A3_KEYS_DIR = "{}/keys".format(A3_SERVER_DIR)
WORKSHOP_MODS = {} # Loaded names and ids from workshop, WORKSHOP_MODS[mod_name] = mod_id
MODS = [] # The list of mod names to start with

WORKSHOP_ID_REGEX = re.compile(r"filedetails\/\?id=(\d+)\"", re.MULTILINE)
LAST_UPDATED_REGEX = re.compile(r"workshopAnnouncement.*?<p id=\"(\d+)\">", re.DOTALL)
MOD_NAME_REGEX = re.compile(r"workshopItemTitle\">(.*?)<\/div", re.DOTALL)
WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"
#endregion

#region Functions
def log(msg):
    print("")
    print("{{0:=<{}}}".format(len(msg)).format(""))
    print(msg)
    print("{{0:=<{}}}".format(len(msg)).format(""))


def call_steamcmd(params):
    print('steamcmd ', params)
    os.system("{} {}".format(STEAM_CMD, params))
    print("")


def env_defined(key):
    return key in os.environ and len(os.environ[key]) > 0


def update_server():
    steam_cmd_params  = " +login {} {}".format(STEAM_USER, STEAM_PASS)
    steam_cmd_params += " +force_install_dir {}".format(A3_SERVER_DIR)
    steam_cmd_params += " +app_update {}".format(A3_SERVER_ID)
    if env_defined("STEAM_BRANCH"):
        steam_cmd_params += " -beta {}".format(os.environ["STEAM_BRANCH"])
    if env_defined("STEAM_BRANCH_PASSWORD"):
        steam_cmd_params += " -betapassword {}".format(os.environ["STEAM_BRANCH_PASSWORD"])
    steam_cmd_params += " validate +quit"

    call_steamcmd(steam_cmd_params)


def copy_mod_keys(moddir):
    keysdir = os.path.join(moddir, "keys")
    if os.path.exists(keysdir):
        for o in os.listdir(keysdir):
            keyfile = os.path.join(keysdir, o)
            if not os.path.isdir(keyfile):
                shutil.copy2(keyfile, A3_KEYS_DIR)
    else:
        print("Missing keys:", keysdir)


def download_workshop_mod(mod_id):
    steam_cmd_params  = " +login {} {}".format(STEAM_USER, STEAM_PASS)
    steam_cmd_params += " +force_install_dir {}".format(A3_SERVER_DIR)
    steam_cmd_params += " +workshop_download_item {} {} validate".format(
        A3_WORKSHOP_ID,
        mod_id
    )
    steam_cmd_params += " +quit"
    call_steamcmd(steam_cmd_params)


def lowercase_workshop_dir(path):
    os.system("(cd {} && find . -depth -exec rename -v 's/(.*)\/([^\/]*)/$1\/\L$2/' {{}} \;)".format(path))


def check_workshop_mod(mod_id):
    response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read().decode("utf-8")
    mod_name = MOD_NAME_REGEX.search(response).group(1)
    mod_last_updated = LAST_UPDATED_REGEX.search(response)
    path = "{}/{}".format(A3_WORKSHOP_DIR, mod_id)

    if mod_last_updated:
        updated_at = datetime.fromtimestamp(int(mod_last_updated.group(1)))
        created_at = datetime.fromtimestamp(os.path.getctime(path))
        if (updated_at >= created_at):
            shutil.rmtree(path)
    
    if not os.path.isdir(path):
        print("Updating \"{}\" ({})".format(mod_name, mod_id))
        download_workshop_mod(mod_id)
    else:
        print("No update required for \"{}\" ({})... SKIPPING".format(mod_name, mod_id))
    
    copy_mod_keys(path)
    lowercase_workshop_dir(path)
    WORKSHOP_MODS[mod_name] = mod_id


def load_workshop_mods():
    mod_file = os.environ["WORKSHOP_MODS"]
    if (mod_file == ''):
        log("WORKSHOP_MODS env variable not set, nothing to do.")
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


def load_local_mods(): # Should be called before create_mod_symlinks
    for mod_folder_name in os.listdir(A3_MODS_DIR):
        local_mod_path = os.path.join(A3_MODS_DIR, mod_folder_name)
        if os.path.isdir(local_mod_path) and not os.path.islink(local_mod_path):
            print("Found local mod \"{}\"".format(mod_folder_name))
            MODS.append(local_mod_path)
            copy_mod_keys(local_mod_path)


def create_mod_symlinks():
    for mod_name, mod_id in WORKSHOP_MODS.items():
        link_path = "{}/@{}".format(A3_MODS_DIR, mod_name)
        real_path = "{}/{}".format(A3_WORKSHOP_DIR, mod_id)

        if os.path.isdir(real_path):
            MODS.append(link_path)
            if not os.path.islink(link_path):
                print("Creating symlink '{}'...".format(link_path))
                os.symlink(real_path, link_path)
        else:
            print("Mod '{}' does not exist! ({})".format(mod_name, real_path))
#endregion

log("Updating A3 server ({})".format(A3_SERVER_ID))
update_server()

log("Loading and updating workshop mods...")
load_workshop_mods()
print("Workshop mods loaded", WORKSHOP_MODS)

log("Adding local/server mods...")
load_local_mods()

log("Creating workshop symlinks...")
create_mod_symlinks()

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
