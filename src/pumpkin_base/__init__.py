from pumpkin.repository import Repository, Module


r_base = Repository(name="base", package="pumpkin_base")

m_acl = Module(
    "acl",
    r_base,
    "pumpkin_base.acl.module",
    "ACL",
)
m_admin = Module(
    "admin",
    r_base,
    "pumpkin_base.admin.module",
    "Admin",
    database="pumpkin_base.admin.database",
)
m_base = Module(
    "base",
    r_base,
    "pumpkin_base.base.module",
    "Base",
    database="pumpkin_base.base.database",
)
m_errors = Module(
    "errors",
    r_base,
    "pumpkin_base.errors.module",
    "Errors",
    database="pumpkin_base.errors.database",
)
m_info = Module(
    "info",
    r_base,
    "pumpkin_base.info.module",
    "Info",
)
m_language = Module(
    "language",
    r_base,
    "pumpkin_base.language.module",
    "Language",
)
m_logging = Module(
    "logging",
    r_base,
    "pumpkin_base.logging.module",
    "Logging",
)


def repo() -> Repository:
    return r_base
