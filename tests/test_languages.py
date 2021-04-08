from .language_file_checker import Module


def test_language_files():
    assert None is Module("core/").result
    assert None is Module("modules/base/admin/").result
    assert None is Module("modules/base/base/").result
    assert None is Module("modules/base/errors/").result


# TODO Test substitutions
# TODO Test database stuff
