import pathlib

l10n = pathlib.Path(__file__).parent / "po"


def main():
    import pumpkin.cli

    pumpkin.cli.main()
