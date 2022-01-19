from __future__ import annotations

import git
import hashlib
import re
import subprocess  # nosec: B404
import sys
from pathlib import Path
from typing import List, Tuple, Optional


RE_QUOTE = r"(\"|\"\"\"|')"
RE_NAME = r"[a-z_][0-9a-z_]+"
RE_NAMES = r"[a-z0-9_,\s" + RE_QUOTE + r"]+"


class RepositoryManager:
    """Module repository manager.

    :param repositories: List of found repositories.
    :param log: Information about repository manager actions.
    """

    repositories: List[Repository]
    log: List[str]

    def __init__(self):
        self.log = []
        self.refresh()

    def refresh(self):
        self.repositories = self.get_repositories()

    def flush_log(self):
        self.log = []

    def get_repositories(self) -> List[Repository]:
        """Scan for available repositories."""
        repositories: List[Repository] = []

        repo_dir: Path = Path("modules/").resolve()
        found_dirs: List[Path] = sorted(
            [d for d in repo_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
        )

        for directory in found_dirs:
            # test for signs of the directory being a repository
            if not (directory / "__init__.py").is_file():
                continue

            # try to initiate the repository
            try:
                repository = Repository(directory)
            except Exception as exc:
                self.log.append(
                    f"Directory '{directory.name}' is not a repository: {exc}"
                )
                continue

            # no error found, the directory is a repository
            repositories.append(repository)

        return repositories

    def get_repository(self, name: str) -> Optional[Repository]:
        """Get repository by its name."""
        for repository in self.repositories:
            if repository.name == name:
                return repository
        return None


class Repository:
    """Module repository."""

    __slots__ = ("path", "branch", "name", "module_names")

    path: Path
    branch: str
    name: str
    module_names: Tuple[str]

    def __init__(self, path: Path, branch: Optional[str] = None):
        self.path: Path = path
        if branch is not None:
            self.change_branch(branch)
        self.set_facts()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} path={self.path!s} "
            f"name='{self.name}' modules='{', '.join(self.module_names)}'>"
        )

    def change_branch(self, branch: str) -> None:
        """Change the git branch of the repository.

        :raises ValueError: Output of git if an error occurs.
        """
        is_base: bool = getattr(self, "name", "") == "base"
        repo = git.repo.base.Repo(str(self.path), search_parent_directories=is_base)
        repo.remotes.origin.fetch()
        try:
            repo.git.checkout(branch)
        except git.exc.GitCommandError as exc:
            raise ValueError(
                f"Could not checkout branch '{branch}': {exc.stderr.strip()}"
            )

    def set_facts(self):
        """Check the __init__.py and get information from there."""
        init: Path = self.path / "__init__.py"
        if not init.is_file():
            return {}

        name: Optional[str] = None
        module_names: Optional[Tuple[str]] = None

        with open(init, "r") as handle:
            for line in handle.readlines():
                line = line.strip()
                if "=" not in line:
                    continue

                if line.startswith("__name__"):
                    name = self._regex_get_name(line)
                if line.startswith("__all__"):
                    module_names = self._regex_get_modules(line)

        if name is None:
            raise ValueError(
                f"Specification of a repository at '{self.path}' is missing a name."
            )
        if module_names is None:
            raise ValueError(
                f"Specification of a repository at '{self.path}' "
                "is missing a list of modules."
            )
        for module_name in module_names:
            if not (self.path / module_name).is_dir():
                raise ValueError(
                    f"Specification of a repository at '{self.path}' "
                    f"includes link to invalid module '{module_name}'."
                )

        self.name = name
        self.module_names = module_names

    def _regex_get_name(self, line: str) -> str:
        """Get name from line using regex."""
        regex: str = (
            r"(__name__)(\s*)(=)(\s*)" + RE_QUOTE + "(" + RE_NAME + ")" + RE_QUOTE
        )
        matched: Optional[re.Match] = re.fullmatch(regex, line)
        if matched is None:
            raise ValueError(f"Repository at '{self.path}' has invalid name.")
        name: str = matched.groups()[-2]
        return name

    def _regex_get_modules(self, line: str) -> Tuple[str]:
        """Get tuple of module names using regex."""
        regex: str = r"(__all__)(\s*)(=)(\s*)" + r"\((" + RE_NAMES + r")\)"
        matched: Optional[re.Match] = re.fullmatch(regex, line)
        if matched is None:
            raise ValueError(
                f"Repository at '{self.path}' has "
                "invalid specification of included modules."
            )
        names: str = matched.groups()[-1]
        list_of_names = [n.strip(" \"'") for n in names.split(",")]
        list_of_names = [n for n in list_of_names if len(n)]
        for name in list_of_names:
            if re.fullmatch(RE_NAME, name) is None:
                raise ValueError(
                    f"Repository at '{self.path}' specification "
                    f"contains invalid name for included module '{name}'."
                )
            if not (self.path / name / "__init__.py").is_file():
                raise ValueError(f"Module '{name}' is missing its init file.")
            if not (self.path / name / "module.py").is_file():
                raise ValueError(f"Module '{name}' is missing its module file.")
        return tuple(list_of_names)

    @staticmethod
    def git_clone(path: Path, url: str) -> Optional[str]:
        """Clone repository to given path.

        :return: stderr output on error, otherwise `None`.
        """
        try:
            git.repo.base.Repo.clone_from(url, str(path.resolve()))
        except git.exc.GitError as exc:
            stderr: str = str(exc)[str(exc).find("stderr: ") + 8 :]
            return stderr

    def git_pull(self, force: bool = False) -> str:
        """Perform 'git pull' over the repository.

        :return: Git output
        """
        is_base: bool = self.name == "base"
        repo = git.repo.base.Repo(str(self.path), search_parent_directories=is_base)
        result: str = repo.git.pull(force=force)
        return result

    def git_reset_pull(self) -> str:
        """Perform 'git reset --hard' and 'git pull' over the repository.

        :return: Git output
        """
        is_base: bool = self.name == "base"

        repo = git.repo.base.Repo(str(self.path), search_parent_directories=is_base)

        repo.remotes.origin.fetch()
        result = str(repo.git.reset("--hard", f"origin/{repo.active_branch.name}"))
        result += "\n" + str(repo.git.pull(force=True))
        return result

    @property
    def requirements_txt_hash(self) -> Optional[str]:
        """Get hash of requirements.txt.

        :return: SHA-256 of the file or `None` if it does not exist.
        """
        file: Path = self.path / "requirements.txt"
        if not file.is_file():
            return

        h = hashlib.sha256()
        with open(file, "rb") as handle:
            chunk: int = 0
            while chunk != b"":
                # read 1kB at a time
                chunk = handle.read(1024)
                h.update(chunk)
        file_hash = h.hexdigest()
        return file_hash

    def install_requirements(self) -> Optional[str]:
        """Install packages from requirements.txt.

        :return: Command output if the file exists, otherwise `None`.
        """
        reqirements = self.path / "requirements.txt"
        if not reqirements.is_file():
            return

        output: subprocess.CompletedProcess = subprocess.run(  # nosec: B603
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                reqirements.resolve(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        result = output.stderr or output.stdout
        return result.decode("utf-8")
