"""
Manipulate the CHARACTERS (or DATA) block of a NEXUS file.

Note: Only one option can be chosen at a time.
"""
import collections
from enum import Enum

from commonnexus import Nexus
from commonnexus.blocks.characters import Characters, GAP
from commonnexus.tools.matrix import CharacterMatrix
from commonnexus.tools.combine import combine
from commonnexus.cli_util import add_nexus, add_flag, validate_operations, list_of_ranges


class Ops(Enum):
    binarise = 1
    multistatise = 2
    convert = 3
    drop = 4
    drop_numbered = 5
    describe = 6


def register(parser):
    add_nexus(parser)
    add_flag(
        parser,
        Ops.binarise.name,
        help="Recode a matrix such that it only contains binary characters.")
    parser.add_argument(
        '--' + Ops.multistatise.name,
        metavar="GROUPKEY",
        default=None,
        help="Recode a matrix such that it only contains one multistate characters for each "
             "group of characters as determined by GROUPKEY, a Python lambda function accepting "
             "character label and returning a key (or a string to group all characters into one "
             "multistate character labeled with this string).")
    parser.add_argument(
        '--' + Ops.convert.name,
        choices=['fasta', 'phylip'],
        help="Convert a matrix to another sequence format.")
    parser.add_argument(
        '--' + Ops.drop.name,
        help="Drop specified characters from a matrix.",
        choices='constant polymorphic uncertain missing gapped'.split())
    parser.add_argument(
        '--' + Ops.drop_numbered.name.replace('_', '-'),
        type=list_of_ranges,
        help="Drop characters specified by (ranges of) numbers from a matrix.")
    parser.add_argument(
        '--' + Ops.describe.name,
        help="",
        choices=['binary-setsize', 'binary-unique', 'binary-constant', 'states-distribution'])


def run(args):
    validate_operations(Ops, args)
    new = None
    if args.binarise:
        if args.nexus.characters.FORMAT:  # pragma: no cover
            assert args.nexus.characters.FORMAT.datatype is None or \
                args.nexus.characters.FORMAT.datatype == 'STANDARD'
        _, statelabels = args.nexus.characters.get_charstatelabels()
        new = CharacterMatrix.binarised(args.nexus.characters.get_matrix(), statelabels=statelabels)
    elif args.multistatise:
        if args.multistatise.startswith('lambda'):
            groupkey = eval(args.multistatise)
        else:
            groupkey = lambda c: args.multistatise  # noqa: E731
        charpartitions = collections.defaultdict(list)
        matrix = CharacterMatrix(args.nexus.characters.get_matrix())
        for char in matrix.characters:
            charpartitions[groupkey(char)].append(char)
        matrices = [
            (key, CharacterMatrix.from_characters(matrix, drop_chars=chars, inverse=True))
            for key, chars in charpartitions.items()]
        if len(matrices) == 1:
            new = CharacterMatrix.multistatised(matrices[0][1], multicharlabel=matrices[0][0])
            args.nexus.replace_block(args.nexus.characters, Characters.from_data(new))
            new = args.nexus
        else:
            ms = []
            for key, m in matrices:
                ms.append(CharacterMatrix.multistatised(m, multicharlabel=key))
            new = combine(*[Nexus.from_blocks(Characters.from_data(m)) for m in ms])
        print(new)
        return
    elif args.drop:
        #
        # FIXME: drop unique - for binary matrices
        #
        kw = {'drop_{}'.format(args.drop): True}
        new = CharacterMatrix.from_characters(args.nexus.characters.get_matrix(), **kw)
    elif args.drop_numbered:
        m = CharacterMatrix(args.nexus.characters.get_matrix())
        kw = {'drop_chars': [
            c for i, c in enumerate(m.characters, start=1) if i in args.drop_numbered]}
        new = CharacterMatrix.from_characters(m, **kw)
    elif args.convert:
        m = CharacterMatrix(args.nexus.characters.get_matrix())
        print(getattr(m, 'to_' + args.convert)())
        return
    elif args.describe:
        m = CharacterMatrix(args.nexus.characters.get_matrix())
        chars = m.characters
        chars = collections.OrderedDict([(chars[i], col) for i, col in enumerate(m.iter_columns())])

        if args.describe == 'binary-setsize':
            assert m.is_binary
            args.log.info('Character set sizes (for binary matrix):')
            for k, v in chars.items():
                print('{} {}'.format(k, sum(1 for vv in v if vv and '1' in vv)))
        elif args.describe == 'binary-unique':
            assert m.is_binary
            args.log.info('Unique character sets (for binary matrix):')
            for k, v in chars.items():
                if sum(1 for vv in v if vv and '1' in vv) == 1:
                    print(k)
        elif args.describe == 'binary-constant':
            assert m.is_binary
            args.log.info('Constant characters (for binary matrix):')
            for k, v in chars.items():
                if len(set(v)) == 1:
                    print(k)
        elif args.describe == 'states-distribution':
            args.log.info('State distribution\nchar\tstate\tcount')
            for char, states in chars.items():
                states = collections.Counter(
                    [frozenset(v) if isinstance(v, set) else v for v in states])
                for k, v in states.most_common():
                    print('{}\t{}\t{}'.format(
                        char, '?' if k is None else ('-' if k == GAP else k), v))
        return

    if new:
        args.nexus.replace_block(args.nexus.characters, Characters.from_data(new))
        print(args.nexus)
        return
    matrix = CharacterMatrix(args.nexus.characters.get_matrix())
    args.log.info('{} block with {} taxa and {} characters.'.format(
        args.nexus.characters.name, len(matrix.taxa), len(matrix.characters)))
