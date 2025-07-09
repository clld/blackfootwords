"""
Utility functions used to implement `commonnexus` subcommands.
"""
import re
import sys
import typing
import pathlib
import argparse

from commonnexus import Nexus

NEXUS = re.compile(r'(?:^|(?<=;|\s))(#nexus)', re.IGNORECASE | re.MULTILINE)


class ParserError(Exception):
    pass


class NexusType:
    """
    :class:`Ǹexus` as `Argument type <https://docs.python.org/3/library/argparse.html#type>`_

    Can create :class:`Ǹexus` instances from

    - file paths
    - string content
    - data read from `stdin`
    """
    def __init__(self, many: bool = False):
        self._many = many

    def __call__(self, string):
        if pathlib.Path(string).exists():
            nex = Nexus.from_file(string)
            return [nex] if self._many else nex
        if string == '-':
            string = sys.stdin.read()

        if self._many:
            res = []
            chunks = NEXUS.split(string)
            for i in range(1, len(chunks), 2):
                res.append(Nexus(chunks[i] + chunks[i + 1]))
            return res
        return Nexus(string)


def add_nexus(parser, many=False):
    """
    Adds (a) positional argument(s) `nexus` to the argument parser.

    :param parser:
    :param many:

    .. code-block:: python

        >>> import argparse
        >>> from commonnexus.cli_util import add_nexus
        >>> parser = argparse.ArgumentParser()
        >>> add_nexus(parser)
        >>> args = parser.parse_args(['#nexus begin block; end;'])
        >>> print(args.nexus.BLOCK)
        begin block; end;
        >>> parser = argparse.ArgumentParser()
        >>> add_nexus(parser, many=True)
        >>> args = parser.parse_args(['#nexus begin block; end;', '#nexus begin other; end;'])
        >>> len(args.nexus)
        2
    """
    if many:
        parser.add_argument(
            'nexus',
            help='NEXUS content specified as file path or string or "-" to read from stdin. Note '
                 'that "-" can only be used once. Content from a string or stdin will be split '
                 'into individual NEXUS "files" using the "#NEXUS" token as separator.',
            nargs='+',
            type=NexusType(many=True))
    else:
        parser.add_argument(
            'nexus',
            type=NexusType())


def add_flag(parser, name, help):
    parser.add_argument('--{}'.format(name), action='store_true', default=False, help=help)


def add_rename(parser, what):
    parser.add_argument(
        '--rename',
        help="Rename a {0} specified as 'old,new' where 'old' is the current name or number and "
             "'new' is the new name or as Python lambda function accepting a {0} label as input."
             "".format(what),
        type=lambda s: eval(s) if s.startswith('lambda') else tuple(s.split(',', maxsplit=1)),
        default=None)


def list_of_ranges(dstring) -> typing.List[int]:
    """
    Converts a comma-separated list of 1-based ranges into a list of 1-based indices.

    :param dstring: A string

    :return: `list` of zero-based indices
    """
    def _int(v):
        try:
            return int(v)
        except ValueError:  # pragma: no cover
            raise argparse.ArgumentTypeError("%r is not an integer" % v)

    out = []
    for token in dstring.split(','):
        token = token.replace(':', '-')
        if '-' in token:
            start, stop = token.split("-")
            out.extend([x for x in range(_int(start), _int(stop) + 1)])
        else:
            out.append(_int(token))
    return sorted(out)


def validate_operations(ops, args):
    if sum(1 for op in ops if getattr(args, op.name)) > 1:
        raise ParserError("Only one operation can be specified")  # pragma: no cover
