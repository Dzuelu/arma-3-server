# Docker Arma3 Server

A KISS Arma3 Dedicated Server that can update Arma3 and mods.
Allows for caching steam, Arma3, and mods install OR downloading any (or all) on startup.


### Docker environment parameters
| Parameter               | Required | Default       | Description
| ---                     | ---      | ---           | ---
| ARMA_BINARY             | N        | ./arma3server | Arma 3 server binary to use, `./arma3server_x64` for x64
| ARMA_CDLC               | N        |               | Creator DLC to load. [See](#creator-dlc)
| ARMA_CONFIG             | N        | main.cfg      | Config file to load from `/arma3/configs`
| ARMA_LIMITFPS           | N        | 1000          | Maximum server FPS
| ARMA_PARAMS             | N        |               | Extra parameters given to server and any headless clients
| ARMA_PROFILE            | N        | main          | Profile name, stored in `/arma3/configs/profiles`
| ARMA_WORLD              | N        | empty         | World to load on startup
| DEBUG                   | N        | 0             | Output debug messages including commands run
| FORCE_DOWNLOAD_WORKSHOP | N        | 0             | Force re-download of workshop mods
| HEADLESS_CLIENTS        | N        | 0             | Launch n number of headless clients
| PORT                    | N        | 2302          | Port used by the server, (uses PORT to PORT+3)
| STEAM_BRANCH            | N        | public        | Steam branch code to download. [See](https://community.bistudio.com/wiki/Arma_3:_Steam_Branches)
| STEAM_BRANCH_PASSWORD   | N        |               | Password for Steam branch code
| STEAM_API_KEY           | Y/N      |               | Uses your [steam managed game server api key](https://steamcommunity.com/dev/managegameservers). Replaces user/pass requirement.
| STEAM_PASSWORD          | Y/N      |               | Steam user password
| STEAM_USERNAME          | Y/N      |               | Steam user used to login to steamcmd. Must own Arma3 and can't be used on multiple instances.
| STEAM_VALIDATE          | N        | 1             | Validates files after Steam download
| WORKSHOP_MODS           | N        |               | URL or file path to load mods


### Important directories
| Directory                                | Description
| ---                                      | ---
| /steamcmd                                | Steam cmd executable (not steam install)
| /arma3                                   | Entire Steam install, Arma3 server install, and workshop mods
| /arma3/mpmissions                        | 
| /arma3/configs                           | 
| /arma3/mods                              | Non workshop mods
| /arma3/servermods                        | Server only mods
| /arma3/steamapps/workshop/content/107410 | Steam workshop mods

For quickest startup but larger storage space, recommend saving the `/arma3` volume.
For a smaller storage space, add all the other volumes under `/arma3/` directory.


### Creator DLC
To use a Creator DLC the `STEAM_BRANCH` must be set to `creatordlc` and
then set `ARMA_CDLC` environment variable to the CDLC class name(s) [found here](https://community.bistudio.com/wiki/Category:Arma_3:_CDLCs)
separated by `;`.

Example: `-e ARMA_CDLC=csla;gm;vn;ws`


### Steam workshop mods
The script will check for any workshop mod updates on startup and only download what is out of date.
Place the mod list html exported by the launcher anywhere in the `/arma3/` directory and add the path to `WORKSHOP_MODS` environment variable to load.


### Headless Clients
Launch n number of headless clients when `HEADLESS_CLIENTS` environment variable is set.
Profiles loaded for each headless client will be set to `${ARMA_PROFILE}-hc-${n}`.
For headless clients to connect, you must also have the following in your config cfg file:
```
headlessclients[] = {"127.0.0.1"};
localclient[] = {"127.0.0.1"};
```


### Helpful projects used
[marceldev89](https://gist.github.com/marceldev89/12da69b95d010c8a810fd384cca8d02a), 
[BrettMayson](https://github.com/BrettMayson/Arma3Server)
