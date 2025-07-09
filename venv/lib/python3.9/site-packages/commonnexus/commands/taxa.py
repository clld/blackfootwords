"""
Manipulate the list of TAXA used in a NEXUS file.
"""
import collections

from commonnexus.cli_util import add_nexus, add_flag, ParserError, add_rename
from commonnexus.blocks import Data, Characters, Trees, Taxa, Distances
from commonnexus.blocks.characters import GAP


def register(parser):
    add_nexus(parser)
    parser.add_argument(
        '--drop',
        help="Comma-separated list of taxon labels or numbers to remove from the NEXUS. This will "
             "remove the taxa from the TAXA block, the relevant rows from a CHARACTERS (or DATA) "
             "matrix, and prune the specified taxa from any TREE in a TREES block.",
        type=lambda s: s.split(','),
        default=[])
    add_rename(parser, 'taxon')
    parser.add_argument(
        '--describe',
        help="Describe a named taxon, i.e. aggregate the data for the taxon in a NEXUS file.",
        default=None)
    add_flag(parser, 'check', 'Check whether taxa labels in a NEXUS file are used consistently.')


def run(args):
    taxa = collections.OrderedDict(
        [(str(i), taxon) for i, taxon in enumerate(args.nexus.taxa, start=1)])

    if args.drop or args.rename:
        if args.drop:
            to_drop, to_keep = collections.OrderedDict(), []
            for k, v in taxa.items():
                if k in args.drop or (v in args.drop):
                    to_drop[k] = v
                else:
                    to_keep.append(v)

            if args.nexus.characters:
                matrix = args.nexus.characters.get_matrix()
                for taxon in list(matrix.keys()):
                    if taxon in to_drop or (taxon in to_drop.values()):
                        del matrix[taxon]
                characters = (Data if args.nexus.characters.name == 'DATA' else Characters)\
                    .from_data(matrix)
                args.nexus.replace_block(args.nexus.characters, characters)
            if args.nexus.TREES:
                trees = []
                for tree in args.nexus.TREES.trees:
                    if args.nexus.TREES.TRANSLATE:
                        nwk = args.nexus.TREES.translate(tree)
                    else:
                        nwk = tree.newick
                    nwk.prune_by_names(list(to_drop) + list(to_drop.values()))
                    trees.append((tree.name, nwk, tree.rooted))
                args.nexus.replace_block(args.nexus.TREES, Trees.from_data(*trees))

            if args.nexus.DISTANCES:
                matrix = args.nexus.DISTANCES.get_matrix()
                for taxon in list(matrix.keys()):
                    if taxon in to_drop or (taxon in to_drop.values()):
                        del matrix[taxon]  # pragma: no cover

                for dists in matrix.values():
                    for taxon in list(dists.keys()):
                        if taxon in to_drop or (taxon in to_drop.values()):
                            del dists[taxon]  # pragma: no cover

                args.nexus.replace_block(args.nexus.DISTANCES, Distances.from_data(matrix))

            if args.nexus.NOTES:  # pragma: no cover
                args.log.warning('Changing taxon sets in NOTES block is not supported.')

            if args.nexus.TAXA:
                args.nexus.replace_block(args.nexus.TAXA, Taxa.from_data(to_keep))
            else:
                args.nexus.append_block(Taxa.from_data(to_keep))

        if args.rename:
            mapping = {}
            if callable(args.rename):
                for number, label in taxa.items():
                    new = args.rename(label)
                    if new != label:
                        taxa[number] = mapping[number] = mapping[label] = new
            else:
                old, new = args.rename
                for number, label in taxa.items():
                    if old == number or old == label:
                        taxa[number] = mapping[number] = mapping[old] = new
                        break
                else:
                    raise ParserError('No taxon matching {} found'.format(old))  # pragma: no cover

            if args.nexus.characters:
                matrix = args.nexus.characters.get_matrix()
                if set(matrix).intersection(mapping):
                    matrix = collections.OrderedDict(
                        [(mapping.get(k, k), v) for k, v in matrix.items()])
                    args.nexus.replace_block(args.nexus.characters, Characters.from_data(matrix))
            if args.nexus.DISTANCES:
                matrix = collections.OrderedDict()
                for tax, dists in args.nexus.DISTANCES.get_matrix().items():
                    matrix[mapping.get(tax, tax)] = collections.OrderedDict([
                        (mapping.get(k, k), v) for k, v in dists.items()])
                args.nexus.replace_block(args.nexus.DISTANCES, Distances.from_data(matrix))
            if args.nexus.TREES:
                labels = {}
                if args.nexus.TREES.TRANSLATE:
                    labels = collections.OrderedDict([
                        (k, mapping.get(v, v))
                        for k, v in args.nexus.TREES.TRANSLATE.mapping.items()])
                trees = []
                for tree in args.nexus.TREES.trees:
                    trees.append((tree.name, tree.newick.rename(**mapping), tree.rooted))
                args.nexus.replace_block(args.nexus.TREES, Trees.from_data(*trees, **labels))

            if args.nexus.NOTES:  # pragma: no cover
                args.log.warning('Changing taxon sets in NOTES block is not supported.')

            if args.nexus.TAXA:
                args.nexus.replace_block(args.nexus.TAXA, Taxa.from_data(taxa.values()))
            else:
                args.nexus.append_block(Taxa.from_data(taxa.values()))

        args.nexus.validate(args.log)
        print(args.nexus)
        return

    if args.check:
        if args.nexus.characters:
            mtaxa = list(args.nexus.characters.get_matrix())
            if len(set(mtaxa).intersection(set(taxa).union(taxa.values()))) < len(taxa):
                args.log.warning('Not all taxa appear in characters matrix')
        if args.nexus.DISTANCES:
            args.nexus.DISTANCES.get_matrix()
        if args.nexus.TREES:
            if args.nexus.TREES.TRANSLATE:
                if not set(args.nexus.TREES.TRANSLATE.mapping.values())\
                        .issubset(set(taxa.values())):
                    args.log.error('Invalid taxa labels in TREES TRANSLATE.')
            for tree in args.nexus.TREES.trees:
                nwk = args.nexus.TREES.translate(tree)
                leafnames = {n.name for n in nwk.walk() if n.name and n.is_leaf}
                if not leafnames.issubset(taxa.values()):
                    args.log.error('Invalid taxa labels as leaf name in TREE.')
                names = {n.name for n in nwk.walk() if n.name and not n.is_leaf}
                if not names.issubset(taxa.values()):
                    args.log.warning('Invalid taxa labels as inner node name in TREE.')
        return

    if args.describe:
        for num, name in taxa.items():
            if args.describe in (num, name):
                break
        else:
            raise ValueError('Taxon not found')  # pragma: no cover
        print('# {}\n'.format(name))
        charnotes = collections.defaultdict(list)
        if args.nexus.NOTES:
            for text in args.nexus.NOTES.texts:
                for char in text.characters or []:
                    charnotes[char].append(text.text)
        if args.nexus.characters:
            m = args.nexus.characters.get_matrix(labeled_states=True)
            print('Character | State | Notes')
            print('--- | --- | ---')
            for char, state in m[name].items():
                notes = '/'.join(charnotes.get(char, []))
                print('{} | {} | {}'.format(
                    char, '?' if state is None else ('-' if state == GAP else state), notes))
        if args.nexus.TREES:
            print('\n## Tree {}\n'.format(args.nexus.TREES.TREE.name))
            tree = args.nexus.TREES.translate(args.nexus.TREES.TREE)
            print('```')
            print(tree.ascii_art())
            print('```')
        if args.nexus.NOTES:
            for i, text in enumerate(args.nexus.NOTES.get_texts(taxon=name)):
                if i == 0:
                    print('\n## Notes\n')
                    print('Character | Note')
                    print('--- | ---')
                print('{} | {}'.format('/'.join(text.characters or []), text.text.strip()))
        return

    args.log.info('Taxa:\nnumber\tlabel')
    for i, taxon in taxa.items():
        print('{}\t{}'.format(i, taxon))
