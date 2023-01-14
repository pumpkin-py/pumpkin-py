from typing import Callable, Dict, Optional, Tuple, Type

import discord.ext.commands


# import pumpkin_base.acl.module
# import pumpkin_base.admin.module
# import pumpkin_base.base.module
import pumpkin_base.baseinfo.module
# import pumpkin_base.errors.module
# import pumpkin_base.language.module
# import pumpkin_base.logging.module


def repo() -> Dict[str, Tuple[Type[discord.ext.commands.Cog], Optional[Callable]]]:
    return {
        # "acl": pumpkin_base.acl.module.ACL,
        # "admin": pumpkin_base.admin.module.Admin,
        # "base": pumpkin_base.base.module.Base,
        "baseinfo": (pumpkin_base.baseinfo.module.BaseInfo, None),
        # "errors": pumpkin_base.errors.module.Errors,
        # "language": pumpkin_base.language.module.Language,
        # "logging": pumpkin_base.logging.module.Logging,
    }
