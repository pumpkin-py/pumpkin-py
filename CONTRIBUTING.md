# Contributing

The bot is currently in beta and has no stable API. Things may change.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

**Table of contents**

- [Repository setup](#repository-setup): How to get started with the project
- [Bot setup](#bot-setup): What is needed in order to run the bot in development mode
- [File structure](#file-structure): How the newly created modules should be structured
- [Database](#database): How to create and name module databases
- [Languages](#languages): How to create language files
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


## Import structure

Every file has to be formatted as UTF-8.

All the imports have to be at the top of the `py` file, unles you have **really good** reason to do it differently. For the sake of easy maintenance, the following system should be used:

```py
import local_library_a
import local_library_a.submodule_a
import local_library_b
from loguru import logger
from local_library_b import submodule_b

import thirdparty_library_a
import thirdparty_library_b.submodule_c
from thirdparty_library_c import submodule_d
from thirdparty_library_c import submodule_e

import discord
from discord.ext import commands

from core import text, utils
from .database import RepoModuleTable as Table

tr = text.Translator(__file__).translate


class MyModule(commands.Cog):
    ...
```

Eg. **Python** libraries, **3rd party** libraries, **discord.py** imports and **pumpkin.py** imports, separated by one line of space. Then two empty lines, translation initialisation, one empty line, logging setup, two empty lines and then the class definition. The `setup` function for **discord.py** should be the last thing to be declared in the file.

## Database

All tables defined in `repository/module/database.py` are automatically loaded and created. You SHOULD follow the naming conventions of RepoModuleTable (class) and repo_module_table (table) unless you have really good reason not to do that. For example:

```py
# FILE: economy/bank/database.py
from sqlalchemy import Column, Integer, BigInteger

from database import database, session

class EconomyBankAccounts(database.base):
    __tablename__ = "economy_bank_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    balance = Column(Integer)

    def __repr__(self):
    	return (
    		f'<EconomyBankAccounts guild_id="{self.guild_id}" '
    		f'user_id="{self.user_id}" balance="{self.balance}">'
    	)
```

```py
# FILE: economy/bank/module.py
from .database import EconomyBankAccounts as Accounts
```

## Languages

If the module returns some text, it MUST NOT be hardcoded. Instead, use the `tr =` import:
```py
tr = text.Translator(__file__).translate

...
    def send(self, ctx, *, text: str):
        await ctx.send(tr("send", "reply", text=text))
```

Language INI files should be placed in `lang/` directory inside the module:
```ini
[send]
help = Send the text back
reply =
    You just said:
    > ((text))
```

## Code quality

For your code to be included it has to pass the Github Actions build. You can pretty much ensure this by using the **pre-commit**:

- `pre-commit install`

The code will be tested everytime you create new commit, by manually by running

- `pre-commit run --all`

Every pull request has to be accepted by at least one of the core developers.
