"""
Combine data from multiple NEXUS files and put it in a new one.

The following blocks can be handled:

 - TAXA: Taxa are identified across NEXUS files based on label (not number).
 - CHARACTERS/DATA: Characters are aggregated across NEXUS files (with character labels prefixed,
   for disambiguation).
 - TREES: Trees are (translated and) aggregated across NEXUS files.

"""
import collections

from commonnexus import Nexus
from commonnexus.blocks import Taxa, Trees, Characters

SUPPORTED_BLOCKS = {'TAXA', 'CHARACTERS', 'DATA', 'TREES'}


def combine(*nexus: Nexus, **kw) -> Nexus:
    """
    :param nexus: `Nexus` objects to be combined.
    :return: A new `Nexus` object with the combined data.
    """
    # Make sure we are only dealing with blocks (and datatypes) that we know how to handle.
    for nex in nexus:
        if not kw.get('drop_unsupported', False):
            assert set(nex.blocks).issubset(SUPPORTED_BLOCKS), \
                "Only {} blocks are supported.".format(SUPPORTED_BLOCKS)
        for block in SUPPORTED_BLOCKS:
            assert len(nex.blocks.get(block, [])) <= 1

    # Determine the superset of taxa.
    taxa = []
    for i, nex in enumerate(nexus, start=1):
        for taxon in (nex.taxa or []):
            if taxon not in taxa:
                taxa.append(taxon)

    # Create a super-matrix, with all taxa and all characters.
    matrices, datatypes = [], set()
    charlabels = collections.defaultdict(list)
    for i, nex in enumerate(nexus, start=1):
        if nex.characters:
            datatypes.add(nex.characters.FORMAT.datatype if nex.characters.FORMAT else 'STANDARD')
            matrices.append(nex.characters.get_matrix())
            for chars in matrices[-1].values():
                for charlabel in chars:
                    charlabels[i] = charlabel
                break
    if len(datatypes) > 1:  # pragma: no cover
        raise ValueError('Only CHARACTER or DATA blocks of the same datatype can be combined!')
    matrix = collections.OrderedDict()
    if matrices:
        for taxon in taxa:
            row = collections.OrderedDict()
            for i, m in enumerate(matrices, start=1):
                if taxon in m:
                    for charlabel, val in m[taxon].items():
                        row['{}.{}'.format(i, charlabel)] = val
                else:
                    for charlabel in charlabels[i]:
                        row['{}.{}'.format(i, charlabel)] = None
            matrix[taxon] = row

    # Add all translated trees.
    trees = []
    for i, nex in enumerate(nexus, start=1):
        if nex.TREES:
            for tree in nex.TREES.trees:
                nwk = nex.TREES.translate(tree) if nex.TREES.TRANSLATE else tree.newick
                trees.append(('{}.{}'.format(i, tree.name), nwk, tree.rooted))

    nex = Nexus()
    if taxa:
        nex.append_block(Taxa.from_data(taxa))
    if matrix:
        nex.append_block(Characters.from_data(matrix))
    if trees:
        nex.append_block(Trees.from_data(*trees))

    return nex
