import pathlib

from pumpkin.repository import Repository, Module

l10n = pathlib.Path(__file__).parent / "po"


def repo() -> Repository:
    r_base = Repository(name="base", package="pumpkin_base")

    Module(
        "acl",
        r_base,
        "pumpkin_base.acl.module",
        "ACL",
    )
    Module(
        "admin",
        r_base,
        "pumpkin_base.admin.module",
        "Admin",
        database="pumpkin_base.admin.database",
    )
    Module(
        "base",
        r_base,
        "pumpkin_base.base.module",
        "Base",
        database="pumpkin_base.base.database",
    )
    Module(
        "errors",
        r_base,
        "pumpkin_base.errors.module",
        "Errors",
        database="pumpkin_base.errors.database",
    )
    Module(
        "info",
        r_base,
        "pumpkin_base.info.module",
        "Info",
    )
    Module(
        "language",
        r_base,
        "pumpkin_base.language.module",
        "Language",
    )
    Module(
        "logging",
        r_base,
        "pumpkin_base.logging.module",
        "Logging",
    )

    return r_base
