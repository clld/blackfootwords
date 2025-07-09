import sys
import logging
import pathlib
import argparse
import importlib
import contextlib

import commonnexus
import commonnexus.commands


def get_log(name, level=logging.INFO) -> logging.Logger:
    logging.basicConfig(level=level)
    log = logging.getLogger(name)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log


class Logging(object):
    """
    A context manager to execute a block of code at a specific logging level.
    """

    def __init__(self, logger, level=logging.DEBUG):  # pragma: no cover
        self.level = level
        self.logger = logger
        self.prev_level = self.logger.getEffectiveLevel()
        root = logging.getLogger()
        self.root_logger_level = root.getEffectiveLevel()
        self.root_handler_level = root.handlers[0].level if root.handlers else logging.WARNING

    def __enter__(self):  # pragma: no cover
        self.logger.setLevel(self.level)
        if self.logger.handlers:
            self.logger.handlers[0].setLevel(self.level)
        root = logging.getLogger()
        root.setLevel(self.level)
        if root.handlers:
            root.handlers[0].setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        self.logger.setLevel(self.prev_level)
        root = logging.getLogger()
        root.setLevel(self.root_logger_level)
        if root.handlers:
            root.handlers[0].setLevel(self.root_handler_level)


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def main(args=None, catch_all=False, parsed_args=None, log=None):
    from commonnexus.cli_util import ParserError

    parser = argparse.ArgumentParser(
        prog=commonnexus.__name__,
        description="{} {} is a set of commands to manipulate of files in the NEXUS "
                    "file format.".format(commonnexus.__name__, commonnexus.__version__),
        epilog='See https://github.com/dlce-eva/commonnexus for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # Make logging configurable:
    parser.add_argument('--log', default=get_log(commonnexus.__name__), help=argparse.SUPPRESS)
    parser.add_argument(
        '--log-level',
        default=logging.INFO,
        help='log level [ERROR {}|WARNING {}|INFO {}|DEBUG {}]'.format(
            logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG),
        type=lambda x: getattr(logging, x))
    # Register subcommands:
    subparsers = parser.add_subparsers(
        title="available commands",
        dest="_command",
        description='Run "{} COMAMND -h" to get help for a specific command.'.format(
            commonnexus.__name__),
        metavar="COMMAND")
    for p in sorted(
            pathlib.Path(__file__).parent.joinpath('commands').glob('*.py'),
            key=lambda pp: pp.stem):
        if p.stem == '__init__':
            continue
        mod = importlib.import_module('.{}'.format(p.stem), commonnexus.commands.__name__)
        help = mod.help() if hasattr(mod, 'help') else mod.__doc__
        subparser = subparsers.add_parser(
            p.stem, help=help.strip().splitlines()[0], description=help, formatter_class=Formatter)
        if hasattr(mod, 'register'):
            mod.register(subparser)
        subparser.set_defaults(main=mod.run)

    args = parsed_args or parser.parse_args(args=args)

    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        if not log:  # pragma: no cover
            stack.enter_context(Logging(args.log, level=args.log_level))
        else:
            args.log = log
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:  # pragma: no cover
            print(str(e))
            return main([args._command, '-h'])
        except Exception as e:  # pragma: no cover
            if catch_all:
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
