Halite Game Manager
-------------------

This is a game manager for [Halite](https://halite.io/). Halite is a programming game where players build smart bots that battle head-to-head with the goal of taking over the largest share of a virtual grid.

The small Python script can initiate and run games between Halite bots, producing ranking data to facilitate comparison. It was created in order to make it easy to test and compare different Halite bots locally before submitting.

You can activate/deactivate bots to choose who will play, and then set it to run matches continuously. Ranking data is stored in a sqlite3 database, and the script will print out a table of current skills and ranks as each match completes.

# Installation & Setup

Clone/download this repo.

You'll need Python 3, which you can find [here](https://www.python.org/) if you don't already have it.

You'll also need the ['skills' module](https://pypi.python.org/pypi/skills) which can be installed through [Pip](https://pypi.python.org/pypi/pip):

`pip install skills`

Note that you'll also need the game environment for Halite. Presumably you'll have this already if you've been participating in the competition, but if not, you can find it [here](https://halite.io/downloads.php).

You may need to modify a few variables in the `manager.py` script:

```
halite_command = "./halite"  
replay_dir = "replays"
```

e.g. if you're running on Windows, with the game environment halite.exe located in the same folder as `manager.py`, then you can use:

`halite_command = "./halite.exe"`

You can also direct the replays to a different directory if you wish to (or disable saving of the replays altogether using the `-n` argument specified below.

# Running the game manager

First you'll need to add two or more bots by running `manager.py` with the `-A` argument, specifying the name and path for the bot:

`python3 manager.py -A MyBot -p "python3 C:\Projects\halite\MyBot.py"`  
`python3 manager.py -A RandomBot -p "python3 C:\Projects\halite\RandomBot.py"`  

(obviously the above will vary depending on your OS and python/path setup etc)

Then simply run `manager.py`, making use of the optional arguments below as needed/desired.

e.g. `python3 manager.py -n` (to run without storing replays)

Optional arguments:

| argument | name | description |
| --- | --- | --- |
|  -h | HELP |          Show this help message and exit |
|  -A | ADDBOT |           Add a new bot with a name |
|  -D | DELETEBOT |        Delete the named bot |
|  -a | ACTIVATEBOT |      Activate the named bot |
|  -d | DEACTIVATEBOT |    Deactivate the named bot |
|  -p | BOTPATH |          Specify the path for a new bot |
|  -r | SHOWRANKS |        Show a list of all bots, ordered by skill |
|  -m | MATCH |            Run a single match |
|  -f | FOREVER |          Run games forever (or until interrupted) |
|  -n | NOREPLAYS |         Do not store replays |

The [add_bot.sh](https://github.com/smiley1983/halite-match-manager/blob/master/add_bots.sh) script shows an example of adding many bots at once.

# Contributions
  
If you discover any bugs, please feel free to open issues on the Github page (or issue pull requests if you have fixes) - I'll try to attend to them but can't make any promises.
