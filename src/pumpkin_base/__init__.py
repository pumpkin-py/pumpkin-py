from typing import Callable, Dict, Optional, Tuple

import pumpkin_base.admin.database
import pumpkin_base.base.database
import pumpkin_base.errors.database


def repo() -> Dict[str, Tuple[str, Optional[Callable]]]:
    return {
        "acl": (
            "pumpkin_base.acl.module.ACL",
            None,
        ),
        "admin": (
            "pumpkin_base.admin.module.Admin",
            pumpkin_base.admin.database,
        ),
        "base": (
            "pumpkin_base.base.module.Base",
            pumpkin_base.base.database,
        ),
        "baseinfo": ("pumpkin_base.baseinfo.module.BaseInfo", None),
        "errors": (
            "pumpkin_base.errors.module.Errors",
            pumpkin_base.errors.database,
        ),
        "language": (
            "pumpkin_base.language.module.Language",
            None,
        ),
        "logging": (
            "pumpkin_base.logging.module.Logging",
            None,
        ),
    }
