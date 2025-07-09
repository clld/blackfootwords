"""
Normalise a NEXUS file.

Normalisation includes

 - converting CHARACTERS/DATA matrices to non-transposed, non-interleaved representation with
   taxon labels (and resolved EQUATEs), extracting taxon labels into a TAXA block;
 - converting a DISTANCES matrix to non-interleaved matrices with diagonal and both triangles
   and taxon labels;
 - translating all TREEs in a TREES block (such that the TRANSLATE command becomes superfluous).

In addition, after normalisation, the following assumptions hold:

- All commands start on a new line.
- All command names (**not** block names) are in uppercase with no "in-name-comment",
  like "MA[c]TRiX"
- The ";" terminating MATRIX commands is on a separate line, allowing more simplistic parsing
  of matrix rows.
"""
import typing
import collections

import newick

from commonnexus import Nexus
from commonnexus.blocks.characters import Data
from commonnexus.blocks import Taxa, Distances, Characters, Trees


def normalise(nexus: Nexus,
              data_to_characters: bool = False,
              strip_comments: bool = False,
              remove_taxa: typing.Optional[typing.Container[str]] = None,
              rename_taxa: typing.Optional[
                  typing.Union[typing.Callable[[str], str], typing.Dict[str, str]]] = None,
              ) -> Nexus:
    """
    Normalise a `Nexus` object as described above.

    :param nexus: A `Nexus` object to be normalised in-place.
    :param data_to_characters: Flag signaling whether DATA blocks should be converted to CHARACTER \
    blocks.
    :param strip_comments: Flag signaling whether to remove all non-command comments.
    :param remove_taxa: Container of taxon labels specifying taxa to remove from relevant blocks.
    :param rename_taxa: Specification of taxa to rename; either a ``dict``, mapping old names to \
    new names, or a callable, accepting the old name as sole argument and returning the new name.
    :return: The modified `Nexus` object.

    .. warning::

        ``remove_taxa`` and ``rename_taxa`` only operate on TAXA, CHARACTERS/DATA, DISTANCES and
        TREES blocks. Thus, normalisation may result in an inconsistent NEXUS file, if the file
        contains other blocks which reference taxa (e.g. NOTES).

    .. code-block:: python

        >>> from commonnexus import Nexus
        >>> from commonnexus.tools import normalise
        >>> print(normalise(Nexus('''#NEXUS
        ... BEGIN CHARACTERS;
        ... DIMENSIONS NCHAR=3;
        ... FORMAT DATATYPE=STANDARD MISSING=x GAP=- SYMBOLS="01" INTERLEAVE;
        ... MATRIX
        ...     t1 10
        ...     t2    01
        ...     t3    00
        ...     t1 0
        ...     t2 0
        ...     t3 1;
        ... END;
        ... BEGIN DISTANCES;
        ... DIMENSIONS NTAX=3;
        ... FORMAT NODIAGONAL MISSING=?;
        ... MATRIX
        ...     t1
        ...     t2    1.0
        ...     t3    2.0 3.0;
        ... END;
        ... BEGIN TREES;
        ... TRANSLATE a t1, b t2, c t3;
        ... TREE 1 = (a,b,c);
        ... END;''')))
        #NEXUS
        BEGIN TAXA;
        DIMENSIONS NTAX=3;
        TAXLABELS t1 t2 t3;
        END;
        BEGIN CHARACTERS;
        DIMENSIONS NCHAR=3;
        FORMAT DATATYPE=STANDARD MISSING=? GAP=- SYMBOLS="01";
        MATRIX
        t1 100
        t2 010
        t3 001
        ;
        END;
        BEGIN DISTANCES;
        DIMENSIONS NTAX=3;
        FORMAT TRIANGLE=BOTH MISSING=?;
        MATRIX
        t1 0 1.0 2.0
        t2 1.0 0 3.0
        t3 2.0 3.0 0
        ;
        END;
        BEGIN TREES;
        TREE 1 = (t1,t2,t3);
        END;
    """
    remove_taxa = remove_taxa or []

    def rename_taxon(s):
        if rename_taxa is None:
            return s
        if isinstance(rename_taxa, dict):
            return rename_taxa.get(s, s)
        return rename_taxa(s)

    if strip_comments:
        nexus = Nexus([cmd.without_comments() for cmd in nexus], config=nexus.cfg)
    nexus = Nexus([cmd.with_normalised_whitespace() for cmd in nexus], config=nexus.cfg)

    taxlabels = None
    if nexus.characters:
        matrix = nexus.characters.get_matrix()
        taxlabels = list(matrix.keys())
        matrix = collections.OrderedDict(
            (rename_taxon(k), v) for k, v in matrix.items() if k not in remove_taxa)
        characters = nexus.DATA or nexus.CHARACTERS
        cls = Data if characters.name == 'DATA' and not data_to_characters else Characters
        nexus.replace_block(
            characters,
            cls.from_data(matrix, statelabels=nexus.characters.get_charstatelabels()[1]))

    if nexus.DISTANCES:
        matrix = nexus.DISTANCES.get_matrix()
        if taxlabels:
            assert set(matrix.keys()).issubset(taxlabels)
        else:
            taxlabels = list(matrix.keys())
        matrix = collections.OrderedDict(
            (rename_taxon(k), collections.OrderedDict(
                (rename_taxon(kk), vv) for kk, vv in v.items() if kk not in remove_taxa))
            for k, v in matrix.items() if k not in remove_taxa)
        nexus.replace_block(nexus.DISTANCES, Distances.from_data(matrix))

    if nexus.TREES:
        def rename(n):
            if n.name:
                new = rename_taxon(n.unquoted_name)
                n.name = newick.Node(new, auto_quote=True).name

        trees = []
        for tree in nexus.TREES.trees:
            nwk = nexus.TREES.translate(tree) if nexus.TREES.TRANSLATE else tree.newick
            if remove_taxa:
                nwk.prune_by_names(remove_taxa)
            nwk.visit(rename)
            trees.append((tree.name, nwk, tree.rooted))
        nexus.replace_block(nexus.TREES, Trees.from_data(*trees))

    if taxlabels:
        taxlabels = [rename_taxon(t) for t in taxlabels]
        taxa = Taxa.from_data([t for t in taxlabels if t not in remove_taxa])
        if nexus.TAXA:
            assert nexus.TAXA.DIMENSIONS.ntax == len(taxlabels)
            assert set(nexus.TAXA.TAXLABELS.labels.values()) == set(taxlabels)
            nexus.replace_block(nexus.TAXA, taxa)
        else:
            nexus.prepend_block(taxa)
    return nexus
