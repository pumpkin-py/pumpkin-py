# Contributing

The code is currently in heavy development and will change a lot.

## Repository setup

- Fork the repository
- Clone your fork
- Add upstream: `git remote add upstream git@github.com:Pumpkin-py/pumpkin.py.git`
- Create your feature branch: `git checkout main && git branch my-feature && git checkout my-feature`
- Open your pull requests from this branch.

## Development setup

- Install bot packages: `pip3 install -r requirements.txt`
- Install dev packages: `pip3 install -r requirements-dev.txt`
- Enable pre-commit: `pre-commit install`
- Fill and load `.env` file: `set -o allexport; source .env; set +o allexport`
