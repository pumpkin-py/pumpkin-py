# nosec: B101

import git
import os
import tempfile

from modules.base.admin import Admin


def _create_repo(path: str):
    git.repo.base.Repo.init(path=path, bare=True)


def _update_init(
    path: str,
    *,
    name: str = "test",
    modules: tuple = ("test",),
    version: str = "0.1.2",
    create_modules: bool = True,
):
    """Update __init__.py file"""
    with open(os.path.join(path, "__init__.py"), "w") as handle:
        module_names = [f'"{m}"' for m in modules]
        handle.write(f'__all__ = ({", ".join(module_names)})\n')
        handle.write(f'__version__ = "{version}"\n')
        handle.write(f'__name__ = "{name}"\n')

    if not create_modules:
        return
    for module in modules:
        try:
            os.mkdir(os.path.join(path, module))
        except FileExistsError:
            pass


def _update_requirements(path: str, *, lines: list):
    """Update requirements.txt file"""
    with open(os.path.join(path, "requirements.txt"), "w") as handle:
        handle.write("\n".join(lines))


def test_module_download():
    """Valid repo clone"""
    # TODO Add when additional repositories are available
    pass


def test_module_install():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)

    info = {
        "all": ("test", "test-test"),
        "name": "test",
        "version": "0.1.2",
    }
    _update_init(
        tempdir.name,
        name=info["name"],
        version=info["version"],
        modules=info["all"],
    )

    result = Admin._verify_module_repo(path=tempdir.name)
    assert result[0] is True
    assert result[1] == "ok"
    assert result[2]["all"] == info["all"]
    assert result[2]["name"] == info["name"]
    assert result[2]["version"] == info["version"]

    tempdir.cleanup()


def test_module_install_failures():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)

    _update_init(tempdir.name, name="CAPITALS")
    result = Admin._verify_module_repo(path=tempdir.name)
    assert result[0] is False
    assert result[1] == "invalid name"

    _update_init(tempdir.name, name="")
    result = Admin._verify_module_repo(path=tempdir.name)
    assert result[0] is False
    assert result[1] == "invalid name"

    _update_init(tempdir.name, modules=("CAPITALS",))
    result = Admin._verify_module_repo(path=tempdir.name)
    assert result[0] is False
    assert result[1] == "invalid module name"

    _update_init(tempdir.name, modules=("missing",), create_modules=False)
    result = Admin._verify_module_repo(path=tempdir.name)
    assert result[0] is False
    assert result[1] == "missing module"

    tempdir.cleanup()


def test_requirements_install():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)

    result = Admin._install_module_requirements(path=tempdir.name)
    assert result is None

    _update_requirements(tempdir.name, lines=("wheel",))
    result = Admin._install_module_requirements(path=tempdir.name)
    assert result.returncode == 0

    _update_requirements(tempdir.name, lines=("00000000000000000",))
    result = Admin._install_module_requirements(path=tempdir.name)
    assert result.returncode != 0

    tempdir.cleanup()
