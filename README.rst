==============
package_parser
==============
Python utility for parsing packages names and versions from wheel filename, sdist filenames, or setup.py files


Example
=======

Manually import py files or .pyd files

.. code-block:: python

    from package_parser import parse, normalize_name

    attrs = parse('class-property-1.0.0-py3-none-any.whl')
    assert normalize_name(attrs['name']) == 'class_property'
    assert attrs['version'] == '1.0.0'
