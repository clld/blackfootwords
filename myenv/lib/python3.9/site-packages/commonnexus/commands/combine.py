import itertools

from commonnexus.tools import combine
from commonnexus.cli_util import add_nexus


def help():
    return combine.__doc__


def register(parser):
    add_nexus(parser, many=True)
    parser.add_argument(
        '--drop-unsupported',
        help='Drop NEXUS blocks that cannot be combined.',
        action='store_true',
        default=False)


def run(args):
    kw = {}
    if args.drop_unsupported:
        kw['drop_unsupported'] = True
    print(combine.combine(*list(itertools.chain(*args.nexus)), **kw))
