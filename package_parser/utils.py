import os
import re
import sys
import inspect
from packaging.tags import sys_tags, parse_tag
from packaging.utils import canonicalize_name, canonicalize_version
from packaging.version import Version, InvalidVersion


__all__ = [
    'parse',
    'normalize_name', 'is_compatible', 'get_compatibility_tags', 'get_supported', 'SUPPORTED',
    'parse_wheel_filename', 'parse_sdist_filename', 'parse_custom', 'parse_meta', 'parse_setup', 'parse_module',
    'remove_possible_md5', 'try_attrs']


_CONVERT_UNDERSCORE = re.compile("[^\w]+")


def normalize_name(name):
    """Normalize the name by replacing '-' and other invalid characters with a '_'."""
    return _CONVERT_UNDERSCORE.sub('_', str(name))


def get_supported():
    """Return a list of supported tags."""
    tags = [(t.interpreter, t.abi, t.platform) for t in sys_tags()]
    for t in list(tags):
        if t[1].startswith('cp'):
            tags.append((t[0], t[1]+'m', t[2]))  # Copy tags with 'm' added to the abi
    return tags


SUPPORTED = get_supported()


def get_compatibility_tags(filename):
    """Get the python version and os architecture to check against.

    Args:
        filename (str): Wheel filename that ends in .whl or sdist filename that ends with .tar.gz.

    Returns:
        pyver (str)['py3']: Python version of the library py3 or cp38 ...
        abi (str)['none']: ABI version abi3, none, cp33m ...
        plat (str)['any']: Platform of the library none, win32, or win_amd64
    """
    # Parse the wheel filename or sdist filename
    attrs = parse(filename)

    # Assume correct version if not found.
    return (attrs.get('pyver', 'py{}'.format(sys.version_info[0])),
            attrs.get('abi', 'none'),
            attrs.get('plat', 'any'))


def is_compatible(filename):
    """Return if the given filename is available on this system."""
    pyver, abi, plat = get_compatibility_tags(filename)
    return (pyver, abi, plat) in SUPPORTED


def parse(filename):
    """Parse a wheel filename, sdist filename, or setup.py file and return the attributes.

    Args:
        filename (str): Filename that ends in .whl, sdist filename that ends with .tar.gz, or setup.py filename.

    Returns:
        attrs (dict): Dictionary of attributes "name", "version", "build", "pyver", "abi", "plat".
    """
    attrs = {'name': '', 'version': '', 'build': '',
             'pyver': 'py{}'.format(sys.version_info[0]), 'abi': 'none', 'plat': 'any'}

    # Remove md5
    filename = remove_possible_md5(filename)
    try:
        values = parse_wheel_filename(filename)
        attrs.update(values)
    except (AttributeError, ValueError, Exception):
        try:
            values = parse_setup(filename)
            attrs.update(values)
        except (ValueError, AttributeError, Exception):
            try:
                values = parse_meta(filename)
                attrs.update(values)
            except (AttributeError, ValueError, Exception):
                value = parse_custom(filename)  # Parse custom does a little more than parse_sdist
                attrs.update(value)
    return attrs


def parse_wheel_filename(filename):
    """Parse the wheel filename.

    Modified from: https://github.com/pypa/packaging/blob/master/packaging/utils.py

    Returns:
        attributes (dict): Dictionary of attributes "name", "version", "build", "pyver", "abi", "plat".
    """
    # Format the filename
    filename = os.path.basename(filename)
    filename = os.path.splitext(filename)[0]  # Remove ".whl" extension (Do not require this extension)

    # Check number of dashes
    dashes = filename.count("-")
    if dashes < 4:  # Could always have more dashing in the "name" portion
        raise ValueError("Invalid wheel filename (wrong number of parts): {0}".format(filename))

    # Split the filename components
    name, version, pyver, abi, plat = filename.rsplit("-", 4)
    build = ''

    try:
        # Check if name contains version
        if '.' in name:
            raise ValueError  # name contains name and version while version is build?
        ver = Version(version)
    except (InvalidVersion, ValueError, Exception):
        try:
            build = version
            name, version = name.rsplit('-', 1)
            ver = Version(version)  # If this fails it is just invalid
        except (InvalidVersion, ValueError, Exception) as err:
            raise ValueError('Invalid version string "{}"!'.format(version)) from err

    # Check name formatting
    if "__" in name or re.match(r"^[\w\d._]*$", name, re.UNICODE) is None:
        raise ValueError("Invalid project name: {}".format(filename))

    name = canonicalize_name(name)
    return {'name': name, 'version': str(version), 'build': build, 'pyver': pyver, 'abi': abi, 'plat': plat}


def parse_sdist_filename(filename):
    """Parse the sdist filename.

    Modified from: https://github.com/pypa/packaging/blob/master/packaging/utils.py

    Returns:
        attributes (dict): Dictionary of attributes "name", "version".
    """
    # Only parse basename and try to remove md5 if link from pypi/simple
    filename = os.path.basename(filename)
    filename = filename.split('#', 1)[0]

    # Remove extension
    filename = os.path.splitext(filename)[0]  # '.tar.gz', '.zip', '.dist-info'
    if filename.endswith('.tar'):
        filename = os.path.splitext(filename)[0]

    # We are requiring a PEP 440 version, which cannot contain dashes, so we split on the last dash.
    name, version = filename.rsplit('-', 1)
    name = canonicalize_name(name)
    # version = Version(version)
    return {'name': name, 'version': str(version)}


def parse_custom(filename):
    """Parse a filename like a wheel file without a wheel extension.

    Modified from: https://github.com/pypa/packaging/blob/master/packaging/utils.py

    Returns:
        attributes (dict): Dictionary of attributes "name", "version".
    """
    filename = os.path.basename(filename)
    filename = os.path.splitext(filename)[0]  # '.tar.gz', '.zip', '.dist-info'
    if filename.endswith('.tar'):
        filename = os.path.splitext(filename)[0]

    count = filename.count('-')
    if count >= 4:
        count = 4

    # Split the filename
    parts = filename.rsplit('-', count)

    # Find name and version
    name = filename
    version = ''
    if len(parts) >= 2:
        name = canonicalize_name(parts[0])
        version = parts[1]
    if '-' in name:
        split = name.split('-')
        name = split[0]
        version = split[1]

    # Populate attributes
    attrs = {'name': canonicalize_name(name), 'version': version}

    # Find other
    py_ver_found = False
    for item in parts[2:]:  # Skip name and version
        if not py_ver_found and (item.startswith('py') or item.startswith('cp')):
            py_ver_found = True
            attrs['pyver'] = item
        elif item.startswith('cp') or item.startswith('none') or item.startswith('abi'):
            attrs['abi'] = item
        elif item.startswith('any') or item.startswith('win') or item.startswith('linux'):
            attrs['plat'] = item

    return attrs


def parse_meta(filename, required_vars=None):
    """Return the metadata dictionary from the given filename. I started using a __meta__.py file in my projects."""
    if required_vars is None:
        required_vars = ['name', 'version', 'description', 'url', 'author', 'author_email']
    if os.path.isdir(filename):
        filename = os.path.join(filename, '__meta__.py')

    # Meta dictionary
    meta = {}

    try:
        with open(filename, 'r') as f:
            exec(compile(f.read(), filename, 'exec'), meta)
    except (ImportError, Exception):
        pass  # Failed to import and execute the code

    if any(k not in meta for k in required_vars):
        raise ValueError('Invalid __meta__.py file given! Missing some required meta information!')
    return meta


def parse_setup(filename):
    """Parse the setup.py file."""
    if os.path.isdir(filename):
        filename = os.path.join(filename, 'setup.py')
    elif not filename.lower().endswith('setup.py'):
        raise ValueError('Invalid setup.py filename given!')
    basename = os.path.basename(filename)

    # Meta dictionary for setup keyword arguments
    meta = {}
    cwd = None
    orig_setup = None

    try:
        # Change current directory
        cwd = os.getcwd()
        os.chdir(os.path.abspath(os.path.dirname(filename)))

         # First import setuptools
        from setuptools import setup as orig_setup

        # Replace the setuptools "setup" function with custom function
        def my_setup(**attrs):
            meta.update(attrs)

        # Change setup and Save current dir
        sys.modules['setuptools'].setup = my_setup

        try:
            # Compile and execute the setup.py file with the setuptools "setup" function already replaced
            with open(basename, 'r') as f:
                code = compile(f.read(), '<string>', 'exec')
                exec(code, {'__name__': '__main__', '__file__': os.path.abspath(basename)})
        except (ImportError, Exception):
            pass  # Failed to import and execute the code

    except (ImportError, Exception):
        pass  # Failed to import setuptools or invalid setup.py path
    finally:
        # Revert to proper directory and proper setuptools "setup" function
        if orig_setup is not None:
            sys.modules['setuptools'].setup = orig_setup
        if cwd is not None:
            os.chdir(cwd)

    if not meta.get('name', None) or 'version' not in meta:
        raise ValueError('Invalid setup.py file given! Could not get the keyword arguments from the setup function.')

    return meta


def parse_module(module):
    if not inspect.ismodule(module):
        raise ValueError('Module not given!')

    meta = {}
    try:
        meta['name'] = try_attrs(module, '__name__', '__meta__.name')
    except (AttributeError, Exception):
        pass
    try:
        meta['version'] = try_attrs(module, '__version__', '__meta__.version')
    except (AttributeError, Exception):
        pass
    try:
        meta['build'] = try_attrs(module, '__build__', '__meta__.build_id')
    except (AttributeError, Exception):
        pass
    try:
        meta['pyver'] = try_attrs(module, '__pyver__')
    except (AttributeError, Exception):
        pass
    try:
        meta['abi'] = try_attrs(module, '__abi__')
    except (AttributeError, Exception):
        pass
    try:
        meta['plat'] = try_attrs(module, '__plat__')
    except (AttributeError, Exception):
        pass

    if not meta.get('name', None) and 'version' not in meta:
        raise ValueError('Invalid module given! Cannot find a name and version')
    return meta


def remove_possible_md5(filename):
    """Remove the md5 value in the base filename if a link was retrieved from pypi.org/simple."""
    if os.path.isfile(filename) and '#' in os.path.basename(filename):
        filename = os.path.join(os.path.dirname(filename), os.path.basename(filename).split('#', 1)[0])
    return filename


def try_attrs(obj, *attrs, **kwargs):
    """Try to find an available attribute.

    Args:
        obj (object): Object to get the attribute value for.
        *attrs (tuple/str): Tuple of different string attribute names to try (These names may include '.' attributes).
        default (object)[None]: Default Value to return
    """
    if len(attrs) == 0:
        raise TypeError('No attributes given!')

    for attr in attrs:
        this = obj
        try:
            for at in attr.split('.'):
                this = getattr(this, at)
            return this
        except (AttributeError, Exception):
            pass

    if 'default' not in kwargs:
        raise AttributeError('Could not find attribute {} for object {}'.format(attrs[0], obj))
    return kwargs['default']
