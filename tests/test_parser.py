


def test_name_version_wheel():
    from package_parser import parse

    filename = 'dynamicmethod-1.0.3-py3-none-any.whl'
    attrs = parse(filename)
    assert attrs['name'] == 'dynamicmethod', '{} != {}'.format(attrs['name'], 'dynamicmethod')
    assert attrs['version'] == '1.0.3', '{!r} != {!r}'.format(attrs['version'], '1.0.3')

    filename = 'dynamicmethod-1.0.3-cp36-cp36m-any.whl'
    attrs = parse(filename)
    assert attrs['name'] == 'dynamicmethod', '{} != {}'.format(attrs['name'], 'dynamicmethod')
    assert attrs['version'] == '1.0.3', '{} != {}'.format(attrs['version'], '1.0.3')

    filename = 'dynamicmethod-1.0.3dev2-cp36-cp36m-any.whl'
    attrs = parse(filename)
    assert attrs['name'] == 'dynamicmethod', '{} != {}'.format(attrs['name'], 'dynamicmethod')
    assert attrs['version'] == '1.0.3dev2', '{} != {}'.format(attrs['version'], '1.0.3dev2')


def test_name_version_zip():
    from package_parser import parse

    filename = 'dynamicmethod-1.0.2.tar.gz'
    attrs = parse(filename)
    assert attrs['name'] == 'dynamicmethod', '{} != {}'.format(attrs['name'], 'dynamicmethod')
    assert attrs['version'] == '1.0.2', '{} != {}'.format(attrs['version'], '1.0.2')

    filename = 'dynamicmethod-1.0.2.zip'
    attrs = parse(filename)
    assert attrs['name'] == 'dynamicmethod'
    assert attrs['version'] == '1.0.2', '{} != {}'.format(attrs['version'], '1.0.2')


def test_name_version_py():
    from package_parser import parse

    filename = 'custom.py'
    attrs = parse(filename)
    assert attrs['name'] == 'custom', '{} != {}'.format(attrs['name'], 'custom')
    assert attrs['version'] == '', '{} != {}'.format(attrs['version'], '')


def test_name_version_setup_py():
    import pathlib
    from package_parser import parse, parse_setup
    from package_parser import __meta__

    filename = str(pathlib.Path().absolute().parent.joinpath('setup.py'))
    name, version = None, None
    try:
        meta = parse_setup(filename)
        name, version = meta['name'], meta['version']
    except (ImportError, PermissionError, FileNotFoundError, KeyError, Exception):
        pass
    assert name == __meta__.name, '{} != {}'.format(name, __meta__.name)
    assert version == __meta__.version, '{} != {}'.format(version, __meta__.version)


    filename = '../setup.py'  # Local setup.py
    attrs = parse(filename)
    assert attrs['name'] == __meta__.name, '{} != {}'.format(attrs['name'], __meta__.name)
    assert attrs['version'] == __meta__.version, '{} != {}'.format(attrs['version'], __meta__.version)


def test_name_version_meta():
    import os
    from package_parser import parse_meta
    from package_parser import __meta__

    filename = '../setup.py'  # Local setup.py
    name, version = None, None

    # Try finding the __meta__.py file to read. This is the only way I can read the proper name and version.
    filename = os.path.dirname(filename)
    for fname in os.listdir(filename):
        try:
            meta = parse_meta(os.path.join(filename, fname, '__meta__.py'))
            name, version = meta['name'], meta['version']
            break
        except (FileNotFoundError, PermissionError, TypeError, KeyError, Exception):
            pass

    assert name == __meta__.name, '{} != {}'.format(name, __meta__.name)
    assert version == __meta__.version, '{} != {}'.format(version, __meta__.version)


def test_get_compatibility_tags():
    import sys
    import re
    from package_parser import get_compatibility_tags, is_compatible

    pyver = '{}{}'.format(sys.version_info[0], sys.version_info[1])
    filename = 'dynamicmethod-1.0.2rc1-cp{0}-cp{0}m-win_amd64.whl'.format(pyver)
    get_compatibility_tags(filename)

    pyver = '{}{}'.format(sys.version_info[0], sys.version_info[1])
    filename = 'dynamicmethod-1.0.2rc1-cp{0}-cp{0}m-win_amd64.whl'.format(pyver)
    assert is_compatible(filename)

    filename = 'dynamicmethod-1.0.2rc1-cp{0}-cp{0}m-win_amd64.whl'.format(10)
    assert not is_compatible(filename)


def test_parse_module():
    import package_parser

    attrs = package_parser.parse_module(package_parser)
    assert attrs['name'] == 'package_parser'
    assert attrs['version'] == package_parser.__version__


if __name__ == '__main__':
    test_name_version_wheel()
    test_name_version_zip()
    test_name_version_py()
    test_name_version_setup_py()
    test_name_version_meta()
    test_get_compatibility_tags()
    test_parse_module()

    print('All tests finished successfully!')
