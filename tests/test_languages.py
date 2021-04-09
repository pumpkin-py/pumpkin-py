from .language_file_checker import Module


def test_language_files():
    assert None is Module("core/lang").result
    assert None is Module("modules/base/admin/lang").result
    assert None is Module("modules/base/base/lang").result
    assert None is Module("modules/base/errors/lang").result


# TODO Test substitutions
# TODO Test database stuff
