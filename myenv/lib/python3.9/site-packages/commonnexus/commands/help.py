"""
Get help on subcommands.
"""


def register(parser):
    parser.add_argument('command', nargs='?', default=None)


def run(args):
    from commonnexus.__main__ import main

    if args.command:
        return main([args.command, '-h'])
    print('Run "commonnexus COMMAND -h" to get help on subcommand COMMAND')
