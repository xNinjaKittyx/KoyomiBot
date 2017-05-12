Requires the following:

pip install -U discord[voice]
pip install -U redis
pip install -U aiohttp
pip install -U psutil
pip install -U wikipedia

Also requires redis database.

Official Server Support: [Discord Invite](https://discord.gg/Fzz344U)

# Commands

Huge rewrite for Rin Bot. No Bullshit. Just fun stuff.

Prefix = !> for testbot and > for official version.

For the following chart please note that [] means mandatory, and () means optional.

Command | Usage
------------ | -------------
**Anime** |
manga [query] | Gives info on a manga.
anime [query] | Gives info on an anime.
**Comics** |
cyanide | Gives a random Cyanide & Happiness comic.
xkcd | Gives a random XKCD Comic
chrng | Gives a randomly generated Cyanide & Happiness Comic
**Info** |
uptime | Returns the uptime
ping | Returns a ping and a hearbeat...
stats | Shows you stats, and other info    
**Osu!** | 0=Standard, 1=Taiko, 2=CTB, 3=Mania
osusig [player] (0/1/2/3) | Look up an Osu! player
osu [player] (0/1/2/3) | Look up an Osu! player generated signature
**Overwatch** | Regions Supported: eu, kr, na
owrng | Gives a random overwatch hero
owstats [region] [battletag] | Look up Overwatch stats
owteam | Get a random OW Team
**PAD**
pad | Searches a PAD monster
**Random** |
8ball | Ask the 8Ball
flip | Flips a coin.
meow | Random Cat
roll (NdN) | Rolls a dice in NdN format or default to 1d6
woof | Random Dog
choose [choice1] [choice2] (choice3) ... | Chooses between multiple choices.
**Search** |
gfy | Does a search on gyfcat
wiki | Grabs Wikipedia Article
owgif | Random Overwatch Gyfcat
safebooru | Searches Safebooru
Tags:
tag [tagname] | Display tag
tag add [tagname] | It will ask for tag content after determining a name.
tag search [query] | Returns list of tags that contain that query
  *Note:* Tags are only removable by 'Admin' class.
**Wordcount** |
cmdused [cmd] | Shows how many times a cmd has been used.
topwords | Top 10 words used in the server.
blackwords | Words that are not included in wordDB
wordused [word] | Shows how many times a word has been used.
topcmds | Top 10 cmds used.
**​No Category** |
help | Shows the help message.

## To-Do List

* Add more comics like Calvin & Hobbes
* Finish Animehangman (also come up with a better fricking name.)
* Finish Music Player (Have to make it look nice :D)
