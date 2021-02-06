# Contributing

The code is currently in heavy development and will change a lot.

**Table of contents**

- [Repository setup](#repository-setup): How to get started with the project
- [Bot setup](#bot-setup): What is needed in order to run the bot in development mode
- [File structure](#file-structure): How the newly created modules should be structured
- [Code quality](#code-quality): How to run automatic code tests


## Repository setup

- Fork the repository
- Clone your fork
- Add upstream: `git remote add upstream git@github.com:Pumpkin-py/pumpkin.py.git`
- Create your feature branch: `git checkout main && git branch my-feature && git checkout my-feature`
- Open your pull requests from this branch


## Bot setup

```bash
# Download, create and enable venv environment
sudo apt install python3-venv
python3 -m pip install venv
python3 -m venv .venv
source .venv/bin/activate

# Install bot packages
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt

# Enable pre-commit
pre-commit install

# Create and fill .env file (see the table below and the default.env file)
nano .env

# Load .env file
set -o allexport; source .env; set +o allexport
```

| Key | Description |
|-----|-------------|
| DB_STRING | Database connection string |
| TOKEN | Token obtained from [Discord Developers page](https://discord.com/developers) |
| BOT_PREFIX | Prefix character (`!`, `?` or something similar) |
| BOT_MENTIONPREFIX | Whether to react to mentions: `0` or `1`  |
| BOT_GENDER | How the bot should address itself: `f` or `m`    |


## File structure

Every file has to be formatted as UTF-8.

All the imports have to be at the top of the `py` file, unles you have **really good** reason to do it differently. For the sake of easy maintenance, the following system should be used:

```py
import logging
import local_library_a
import local_library_a.submodule_a
import local_library_b
from local_library_b import submodule_b

import thirdparty_library_a
import thirdparty_library_b.submodule_c
from thirdparty_library_c import submodule_d
from thirdparty_library_c import submodule_e

import discord
from discord.ext import commands

from core import text, utils


logging.config.fileConfig("core/log.conf")
logger = logging.getLogger("pumpkin_log")

tr = text.Translator(__file__).translate


class MyModule(commands.Cog):
```

Eg. **Python** libraries, **3rd party** libraries, **discord.py** imports and **pumpkin.py** imports, separated by one line of space. Then two empty lines, logging setup, one empty line, translation initialisation, two empty lines and then the class definition. The `setup` function for **discord.py** should be the last thing to be declared in the file.


## Code quality

For your code to be included it has to pass the Github Actions build. You can pretty much ensure this by using the **pre-commit**:

- `pre-commit install`

The code will be tested everytime you create new commit, by manually by running

- `pre-commit run --all`

Every pull request has to be accepted by at least one of the core developers.
