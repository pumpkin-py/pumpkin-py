from pumpkin.repository import Repository, Module


def repo() -> Repository:
    repo = Repository(name="base", package="pumpkin_base", pip_name="pumpkin")

    Module(
        "acl",
        repo,
        "pumpkin_base.acl.module",
    )
    Module(
        "admin",
        repo,
        "pumpkin_base.admin.module",
    )
    Module(
        "base",
        repo,
        "pumpkin_base.base.module",
        database="pumpkin_base.base.database",
    )
    Module(
        "errors",
        repo,
        "pumpkin_base.errors.module",
        database="pumpkin_base.errors.database",
    )
    Module(
        "info",
        repo,
        "pumpkin_base.info.module",
    )
    Module(
        "language",
        repo,
        "pumpkin_base.language.module",
    )
    Module(
        "logging",
        repo,
        "pumpkin_base.logging.module",
    )

    return repo
