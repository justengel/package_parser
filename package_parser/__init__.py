from .__meta__ import version as __version__

from .utils import parse, \
    is_compatible, get_compatibility_tags, get_supported, SUPPORTED, \
    parse_wheel_filename, parse_sdist_filename, parse_custom, parse_meta, parse_setup, parse_module, \
    remove_possible_md5, try_attrs
