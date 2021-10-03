import git
import pytest
import tempfile
from pathlib import Path
from typing import Union

from modules.base.admin.module import Admin
from modules.base.admin.objects import Repository


def _create_repo(path: str):
    git.repo.base.Repo.init(path=path, bare=True)


def _update_init(
    path: Union[str, Path],
    *,
    name: str = "test",
    modules: tuple = ("test",),
    create_modules: bool = True,
):
    """Update __init__.py file"""
    if path.__class__ == str:
        path = Path(path)

    with open(path / "__init__.py", "w") as handle:
        module_names = ", ".join([f'"{m}"' for m in modules])
        if len(modules) == 1:
            # make sure the written value is tuple, not string
            module_names += ","
        handle.write(f"__all__ = ({module_names})\n")
        handle.write(f'__name__ = "{name}"\n')

    if not create_modules:
        return
    for module in modules:
        _update_module_files(path / module)


def _update_module_files(path: Path):
    """Create files in the module directory."""
    path.mkdir(exist_ok=True)
    with open(path / "__init__.py", "w") as handle:
        handle.write("")
    with open(path / "module.py", "w") as handle:
        handle.write("")


def _update_requirements(path: Path, *, lines: list):
    """Update requirements.txt file"""
    with open(path / "requirements.txt", "w") as handle:
        handle.write("\n".join(lines))


@pytest.mark.skip
def test_module_download():
    """Valid repo clone"""
    # TODO Add when additional repositories are available
    pass


def test_module_check__one_module():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)

    info = {
        "all": ("test",),
        "name": "test",
    }
    _update_init(
        tempdir.name,
        name=info["name"],
        modules=info["all"],
    )

    try:
        repository = Repository(Path(tempdir.name))
        assert repository.name == info["name"]
        assert repository.module_names == info["all"]
    finally:
        tempdir.cleanup()


def test_module_check__more_modules():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)

    info = {
        "all": ("test_a", "test_b"),
        "name": "test",
    }
    _update_init(
        tempdir.name,
        name=info["name"],
        modules=info["all"],
    )

    try:
        repository = Repository(Path(tempdir.name))
        assert repository.name == info["name"]
        assert repository.module_names == info["all"]
    finally:
        tempdir.cleanup()


def test_module_check_failures():
    tempdir = tempfile.TemporaryDirectory()
    _create_repo(tempdir.name)
    temppath = Path(tempdir.name)

    info = {
        "all": ("test",),
        "name": "test",
    }
    _update_init(
        tempdir.name,
        name=info["name"],
        modules=info["all"],
    )

    _update_init(tempdir.name, name="CAPITALS")
    with pytest.raises(ValueError) as excinfo:
        Repository(temppath)
    assert str(excinfo.value) == f"Repository at '{temppath}' has invalid name."

    _update_init(tempdir.name, name="")
    with pytest.raises(ValueError) as excinfo:
        Repository(temppath)
    assert str(excinfo.value) == f"Repository at '{temppath}' has invalid name."

    _update_init(tempdir.name, modules=("CAPITALS",))
    with pytest.raises(ValueError) as excinfo:
        Repository(temppath)
    assert (
        str(excinfo.value)
        == f"Repository at '{temppath}' has invalid specification of included modules."
    )

    _update_init(tempdir.name, modules=("missing",), create_modules=False)
    with pytest.raises(ValueError) as excinfo:
        Repository(temppath)
    assert str(excinfo.value) == "Module 'missing' is missing its init file."

    tempdir.cleanup()


# TODO How to trigger this test with environment variable/parameter?
# https://docs.pytest.org/en/latest/skipping.html?highlight=skipping#id1
@pytest.mark.skip
def test_requirements_install():
    # FIXME Needs updating to current system
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
