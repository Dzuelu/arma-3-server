# Docker Arma3 Server

An Arma3 Dedicated Server that can update Arma3 and mods on startup.
Allows for caching steam, Arma3, and mods install OR downloading any (or all) on startup.


### Creator DLC
To use a Creator DLC the `STEAM_BRANCH` must be set to `creatordlc` and
then set `ARMA_CDLC` environment variable the CDLC class name [found here](https://community.bistudio.com/wiki/Category:Arma_3:_CDLCs)
separated by `;`.

Example: `-e ARMA_CDLC=csla;gm;vn;ws`



### Helpful projects used
[marceldev89](https://gist.github.com/marceldev89/12da69b95d010c8a810fd384cca8d02a), 
[BrettMayson](https://github.com/BrettMayson/Arma3Server)
