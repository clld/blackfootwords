"""
Manipulate a TREES block in a NEXUS file.

Note: Only one option can be chosen at a time.
"""
import enum
import random

from commonnexus.blocks import Trees
from commonnexus.cli_util import (
    add_nexus, add_flag, list_of_ranges, validate_operations, add_rename,
)


class Ops(enum.Enum):
    drop = 1
    sample = 2
    random = 3
    strip_comments = 4
    rename = 5


def register(parser):
    add_nexus(parser)
    parser.add_argument(
        "--drop",
        default=[],
        type=list_of_ranges,
        help="Remove the trees specified as comma-separated ranges of 1-based indices, "
             "e.g. '1', '1-5', '1,20-30'")
    parser.add_argument(
        "--sample",
        type=int,
        metavar='N',
        default=0,
        help="Resample the trees every Nth tree")
    parser.add_argument(
        "--random",
        type=int,
        metavar='N',
        default=0,
        help="Randomly sample N trees from the treefile")
    parser.add_argument(
        '--random-seed',
        help="Set random seed (to a number) to allow for reproducible random sampling.",
        type=lambda s: random.seed(int(s)))
    parser.add_argument(
        "--strip-comments",
        action="store_true",
        default=False,
        help="Remove comments from the trees")
    add_rename(parser, 'tree')
    add_flag(parser, 'describe', 'list 1-based index, names and rooting of trees')


def run(args):
    validate_operations(Ops, args)
    if args.describe:
        args.log.info('Trees\nindex\tname\trooted')
        for i, tree in enumerate(args.nexus.TREES.trees, start=1):
            print('{}\t{}\t{}'.format(i, tree.name, tree.rooted))
        return

    trees = [cmd for cmd in args.nexus.TREES if cmd.name == 'TREE']
    if args.drop:
        for i, tree in enumerate(trees, start=1):
            if i in args.drop:
                args.nexus.remove(tree)
    elif args.sample:
        for i, tree in enumerate(trees, start=1):
            if i % args.sample != 0:
                args.nexus.remove(tree)
    elif args.random:
        sampled = random.sample(trees, args.random)
        for tree in trees:
            if tree not in sampled:
                args.nexus.remove(tree)
    elif args.strip_comments:
        trees = []
        for tree in args.nexus.TREES.trees:
            trees.append((tree.name, tree.newick.strip_comments(), tree.rooted))
        labels = args.nexus.TREES.TRANSLATE.mapping if args.nexus.TREES.TRANSLATE else {}
        args.nexus.replace_block(args.nexus.TREES, Trees.from_data(*trees, **labels))
    elif args.rename:
        trees = []
        for number, tree in enumerate(args.nexus.TREES.trees, start=1):
            tname = tree.name
            if callable(args.rename):
                tname = args.rename(tree.name)
            elif args.rename[0] == str(number) or args.rename[0] == tree.name:
                tname = args.rename[1]
            trees.append((tname, tree.newick, tree.rooted))
        labels = args.nexus.TREES.TRANSLATE.mapping if args.nexus.TREES.TRANSLATE else {}
        args.nexus.replace_block(args.nexus.TREES, Trees.from_data(*trees, **labels))

    print(args.nexus)
