from pumpkin.repository import Repository, Module


def repo() -> Repository:
    r_base = Repository(name="base", package="pumpkin_base")

    Module(
        "acl",
        r_base,
        "pumpkin_base.acl.module",
    )
    Module(
        "admin",
        r_base,
        "pumpkin_base.admin.module",
    )
    Module(
        "base",
        r_base,
        "pumpkin_base.base.module",
        database="pumpkin_base.base.database",
    )
    Module(
        "errors",
        r_base,
        "pumpkin_base.errors.module",
        database="pumpkin_base.errors.database",
    )
    Module(
        "info",
        r_base,
        "pumpkin_base.info.module",
    )
    Module(
        "language",
        r_base,
        "pumpkin_base.language.module",
    )
    Module(
        "logging",
        r_base,
        "pumpkin_base.logging.module",
    )

    return r_base
