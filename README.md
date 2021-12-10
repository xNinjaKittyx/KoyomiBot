![Monogatari](https://xninjakittyx.github.io/KoyomiBot/bg.png)

# KoyomiBot

A Bot that has a lot of random stuff... Provides a lot of different fun, unique commands.


## Features

- Lookup your favorite anime/manga
- Ask for a funny comic from xkcd or explosm
- Random Cat Pic? Fox Pic? Dog Pic?
- Look up dragalia characters (In Progress)
- Foreign Exchange Rates
- Random Gifs
- Typical Music Bot stuff (Still buggy)
- Look up osu! users
- Search through safebooru (warning might have some questionable content), urban dictionary, or wikipedia

## Goals

- Minimal Setup. Should be pretty straightforward to setup.
- No annoying PMs on-join or anything of the sort (plenty of other bots available)
- Just a fun bot to interact with.
- Some Useful integrations with other self-hosted programs.

## Hosting it yourself

I cannot provide any support if you decide to host it yourself. Use at your own risk.

You'll need to first setup docker and docker-compose.

Clone the repository
```
git clone https://github.com/xNinjaKittyx/KoyomiBot.git
```

You can run the wrapper script `./rebuild_and_run.sh`, or run the commands independently in that script.

On first run, it will fail, so you want to take it back down
```
docker-compose down
```

Edit `./koyomibot/config/config.toml` with the proper token values.

Then rerun `./rebuild_and_run.sh` and it should work this time as is.

## Info

- Uses prefix `k>`. Staging bot will use `k!>` for testing

## Useful Links

Official Website (Nothing atm): [GitHubPages](https://xNinjaKittyx.github.io/KoyomiBot)
