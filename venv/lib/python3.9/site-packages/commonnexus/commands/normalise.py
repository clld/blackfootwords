from commonnexus.tools import normalise
from commonnexus.cli_util import add_nexus, add_flag


def help():
    return normalise.__doc__


def register(parser):
    add_nexus(parser)
    add_flag(parser, 'strip-comments', 'Remove non-command comments.')


def run(args):
    print(normalise.normalise(args.nexus, strip_comments=args.strip_comments))
