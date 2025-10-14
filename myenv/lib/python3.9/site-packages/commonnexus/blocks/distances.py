import typing
import decimal
import warnings
import itertools
import collections

from commonnexus.tokenizer import iter_words_and_punctuation, iter_lines, Word
from .base import Block, Payload
from . import characters
from . import taxa

if typing.TYPE_CHECKING:  # pragma: no cover
    from commonnexus import Nexus

ODict = typing.OrderedDict


class Dimensions(characters.Dimensions):
    """
    The NTAX subcommand of this command is needed to process the matrix when some defined taxa are
    omitted from the distance matrix. The NCHAR subcommand is optional and can be used to indicate
    the number of characters for those analyses that need to know how many characters (if any) were
    used to calculate the distances. NCHAR is not required for successful reading of the matrix.
    As for the CHARACTERS and UNALIGNED block, taxa can be defined in a DISTANCES block if NEWTAXA
    precedes the NTAXA subcommand in the DIMENSIONS command. It is advised that new taxa not be
    defined in a DISTANCES block, for the reasons discussed in the description of the DATA block.
    NEWTAXA, if present, must be appear before the NTAX subcommand.

    :ivar bool newtaxa:
    :ivar typing.Optional[int] nchar:
    :ivar int ntax:
    """
    def check(self):
        assert (not self.newtaxa) or self.ntax


class Format(Payload):
    """
    This command specifies the formatting of the MATRIX. The [NO]LABELS and MISSING subcommands are
    as described in the CHARACTERS block.

    1. TRIANGLE = {LOWER | UPPER | BOTH}. This subcommand specifies whether only the lower left
       half of the matrix is present, or only the upper right, or both halves. Below is one example
       of an upper triangular matrix and one of a matrix with both halves included.

       .. code-block::

            BEGIN DISTANCES;
                FORMAT TRIANGLE=UPPER;
                MATRIX
                    taxon_1 0.0  1.0  2.0  4.0  7.0
                    taxon_2      0.0  3.0  5.0  8.0
                    taxon_3           0.0  6.0  9.0
                    taxon_4                0.0 10.0
                    taxon_5                     0.0;
            END;

       .. code-block::

            BEGIN DISTANCES;
                FORMAT TRIANGLE = BOTH;
                MATRIX
                    taxon_1  0    1.0  2.0  4.0  7.0
                    taxon_2  1.0  0    3.0  5.0  8.0
                    taxon_3  2.0  3.0  0    6.0  9.0
                    taxon_4  4.0  5.0  6.0  0   10.0
                    taxon_5  7.0  8.0  9.0 10.0  0;
            END;

    2. DIAGONAL. If DIAGONAL is turned off, the diagonal elements are not included:

       .. code-block::

            FORMAT NODIAGONAL;
            MATRIX
                taxon_1
                taxon_2  1.0
                taxon_3  2.0  3.0
                taxon_4  4.0  5.0  6.0
                taxon_5  7.0  8.0  9.0 10.0;

       If TRIANGLE is not BOTH and DIAGONAL is turned off, then there will be one row that contains
       only the name of a taxon. This row is required. If TRIANGLE=BOTH, then the diagonal must be
       included.
    3. INTERLEAVE. As in the CHARACTERS block, this subcommand indicates sections in the matrix,
       although interleaved matrices take a slightly different form for distance matrices:

       .. code-block::

            taxon_1  0
            taxon_2  1  0
            taxon_3  2  3  0
            taxon_4  4  5  6
            taxon_5  7  8  9
            taxon_6 11 12 13
            taxon_4  0
            taxon_5 10  0
            taxon_6 14 15  0;

       As in the CHARACTERS block, newline characters in interleaved matrices are significant, in
       that they indicate a switch to a new taxon.
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.missing = '?'
        self.labels = True
        self.interleave = False
        self.diagonal = True
        self.triangle = 'LOWER'

        if tokens is None:
            return

        words = iter_words_and_punctuation(self._tokens, nexus=nexus)

        def word_after_equals():
            n = next(words)
            assert n.text == '='
            res = next(words)
            return res if isinstance(res, str) else res.text

        while 1:
            try:
                word = next(words)
                subcommand = None
                if isinstance(word, str):
                    subcommand = word.upper()
                if subcommand in ['TRIANGLE', 'MISSING']:
                    setattr(self, subcommand.lower(), word_after_equals())
                elif subcommand in ['INTERLEAVE']:
                    setattr(self, subcommand.lower(), True)
                elif subcommand in ['NOLABELS', 'LABELS', 'NODIAGONAL', 'DIAGONAL']:
                    setattr(self, subcommand.replace('NO', '').lower(), 'NO' not in subcommand)
            except StopIteration:
                break
        self.triangle = self.triangle.upper()


class Taxlabels(taxa.Taxlabels):
    """
    This command allows specification of the names and ordering of the taxa. It serves to define
    taxa and is allowed only if the NEWTAXA token is included in the DIMENSIONS statement.
    """


class Matrix(Payload):
    """
    This command contains the distance data.

    .. note::

        Since reading the matrix data only makes sense if information from other commands - in
        particular :class:`FORMAT <Format>` - is considered, the ``Matrix`` object does not have
        any attributes for data access. Instead, the matrix data can be read via
        :meth:`Distances.get_matrix`.
    """


class Distances(Block):
    """
    This block contains distance matrices. Taxa are usually not defined in a DISTANCES block; if
    they are not, this block must be preceded by a block that defines taxon labels and ordering
    (e.g., TAXA).
    The syntax of the block is as follows:

    .. rst-class:: nexus

        | BEGIN DISTANCES;
        |   [:class:`DIMENSIONS <Dimensions>` [NEWTAXA] NTAX=num-taxa NCHAR=num-characters;]
        |   [:class:`FORMAT <Format>`
        |     [TRIANGLE={LOWER | UPPER | BOTH}]
        |     [[NO]DIAGONAL]
        |     [[NO]LABELS]
        |     [MISSING=SYMBOL]
        |     [INTERLEAVE]
        |   ;]
        |   [:class:`TAXLABELS <Taxlabels>` taxon-name [taxon-name...];]
        |   :class:`MATRIX <Matrix>` distance-matrix;
        | END;

    Commands must appear in the order listed. Only one of each command is allowed per block.
    """
    __commands__ = [Dimensions, Format, Taxlabels, Matrix]

    def get_matrix(self) -> ODict[str, ODict[str, typing.Union[None, decimal.Decimal]]]:
        """
        :return: A full distance matrix encoded as nested ordered dictionaries.

        .. code-block:: python

            >>> from commonnexus import Nexus
            >>> nex = Nexus('''#NEXUS
            ... BEGIN DISTANCES;
            ...     DIMENSIONS NEWTAXA NTAX=5;
            ...     TAXLABELS taxon_1 taxon_2 taxon_3 taxon_4 taxon_5;
            ...     FORMAT TRIANGLE=UPPER;
            ...     MATRIX
            ...         taxon_1 0.0  1.0  2.0  4.0  7.0
            ...         taxon_2      0.0  3.0  5.0  8.0
            ...         taxon_3           0.0  6.0  9.0
            ...         taxon_4                0.0 10.0
            ...         taxon_5                     0.0;
            ... END;''')
            >>> nex.DISTANCES.get_matrix()['taxon_3']['taxon_1']
            Decimal('2.0')
        """
        format = self.FORMAT or Format(None)

        ntax, taxlabels = None, {}
        if self.DIMENSIONS:
            ntax = self.DIMENSIONS.ntax
        if self.TAXLABELS:
            taxlabels = self.TAXLABELS.labels
            ntax = self.DIMENSIONS.ntax
        elif self.nexus.TAXA:
            taxlabels = self.nexus.TAXA.TAXLABELS.labels
            ntax = self.nexus.TAXA.DIMENSIONS.ntax

        res = collections.OrderedDict()
        label, entries = None, []

        def required_cols(row_index=None):
            # The number of required entries for a distance matrix row depends on TRIANGLE,
            # DIAGONAL and the row index.
            if format.triangle == 'BOTH':  # Each row has entries for all taxa.
                ncols = ntax
            elif format.triangle == 'LOWER':  # Each row has one more entry than the previous one.
                if row_index:
                    ncols = row_index
                else:
                    ncols = 1 if not res else \
                        len(list(res.values())[-1]) + (2 if format.diagonal is False else 1)
            else:  # Each row has one entry less than the previous row.
                if row_index:
                    ncols = ntax - row_index + 1
                else:
                    ncols = ntax - len(list(res.values()))
            if not format.diagonal:
                # And if the diagonal is missing, we expect one entry less in all cases.
                ncols -= 1
            return ncols

        # Now read the matrix data:
        for i, line in enumerate(
            list(iter_lines(self.MATRIX._tokens)) if format.interleave else [self.MATRIX._tokens],
            start=1
        ):
            words = iter_words_and_punctuation(line, nexus=self.nexus)

            if (not format.labels) and required_cols() == 0 and 1 not in res:
                # NODIAGONAL NOLABELS TRIANGLE=LOWER
                res[1] = []

            while 1:
                try:
                    t = next(words)
                    if (format.labels is not False) and label is None:
                        assert isinstance(t, str)
                        label = t
                        if not format.diagonal and not format.interleave and \
                                format.triangle == 'LOWER' and not res:
                            # We're done with this row after the label.
                            res[label] = []
                            label = None
                        continue
                    entries.append(None if t == format.missing else decimal.Decimal(t))
                    if not format.interleave and (len(entries) == required_cols()):
                        res[label or (len(res) + 1)] = entries
                        label, entries = None, []
                except StopIteration:
                    break
            if format.interleave:
                # We collected a row of entries, now append them to the correct taxon.
                # If we have a label, that's easy.
                if not label:
                    for ri in taxlabels:
                        if ri not in res:
                            # First pass must go through all taxa!
                            label = ri
                            break
                    if not label:
                        # The next label to append entries to is the next one still in need of
                        # entries!
                        for row_index in res:
                            if len(res[row_index]) < required_cols(row_index):
                                label = row_index
                                break
                if label not in res:
                    res[label] = []
                res[label].extend(entries)
                label, entries = None, []

        if format.labels is False:
            assert taxlabels
        elif not taxlabels:
            taxlabels = collections.OrderedDict((i, label) for i, label in enumerate(res, start=1))

        # We pad the result rows with None columns on the left as necessary, to make lookup by
        # column index work.
        if format.triangle == 'UPPER':
            for i, key in enumerate(res):
                res[key] = [None] * (i if format.diagonal else i + 1) + res[key]
            if format.diagonal is False and format.labels is False:
                assert (ntax) not in res, str(res.keys())
                res[ntax] = [None]
        elif format.triangle == 'BOTH' and not format.diagonal:
            for i, key in enumerate(res):
                res[key].insert(i, None)

        # Match matrix rows to expected taxa:
        validtaxa = set(str(k) for k in taxlabels).union(taxlabels.values())
        restaxa = {str(k): k for k in res}
        if not set(restaxa).issubset(validtaxa):
            warnings.warn('Pruning undeclared taxa from DISTANCES matrix.')
            for taxon in set(restaxa) - validtaxa:
                del res[restaxa[taxon]]

        if len(res) < len(taxlabels):
            # Not all taxa appear in the matrix. Prune expected taxa to make lookup work.
            for k in list(taxlabels.keys()):
                if (str(k) not in restaxa) and (taxlabels[k] not in restaxa):
                    del taxlabels[k]
            taxlabels = collections.OrderedDict(
                (i, label) for i, label in enumerate(taxlabels.values(), start=1))

        res = {taxlabels.get(k, k): v for k, v in res.items()}
        assert set(res.keys()).issubset(taxlabels.values()), "Unmatched taxa in DISTANCES matrix."

        # Now populate a complete matrix with the data read from the tokens:
        matrix = collections.OrderedDict([
            (label, collections.OrderedDict([(ll, None) for ll in taxlabels.values()]))
            for label in taxlabels.values()])
        for (na, la), (nb, lb) in itertools.combinations_with_replacement(taxlabels.items(), r=2):
            if na == nb and format.diagonal is False:
                matrix[la][lb] = 0
                continue
            if format.triangle == 'BOTH':
                matrix[la][lb] = res[la][nb - 1]
                matrix[lb][la] = res[lb][na - 1]
            else:
                val = res[la][nb - 1] if format.triangle == 'UPPER' else res[lb][na - 1]
                if nb != na:
                    matrix[la][lb] = matrix[lb][la] = val
                else:
                    matrix[la][lb] = val

        return matrix

    @classmethod
    def from_data(cls,
                  matrix: typing.OrderedDict[str, typing.OrderedDict[
                      str, typing.Union[None, float, int, decimal.Decimal]]],
                  taxlabels: bool = False,
                  comment: typing.Optional[str] = None,
                  nexus: typing.Optional["Nexus"] = None,
                  TITLE: typing.Optional[str] = None,
                  ID: typing.Optional[str] = None,
                  LINK: typing.Optional[typing.Union[str, typing.Tuple[str, str]]] = None) \
            -> 'Block':
        """
        Create a DISTANCES block from the distance matrix `matrix`.

        :param matrix: The distance matrix as dict mapping taxon labels to dicts mapping taxon \
        labels to numbers. A "full" matrix is expected here, just like it is returned from \
        :meth:`Distances.get_matrix`.
        :param taxlabels: Whether to include a TAXLABELS command.
        """
        dimensions = 'NTAX={}'.format(len(matrix))
        if taxlabels:
            dimensions = 'NEWTAXA NTAX={} {}'.format(len(matrix), dimensions)
        cmds = [
            # DIMENSIONS: necessary if not all taxa are present in the matrix!
            ('DIMENSIONS', dimensions),
            ('FORMAT', 'TRIANGLE=BOTH MISSING=?'),
        ]
        maxlen, tlabels = 0, {}
        for taxon in matrix:  # We compute maximum taxon label length for pretty printing.
            tlabels[taxon] = Word(taxon).as_nexus_string()
            maxlen = max([maxlen, len(tlabels[taxon])])

        if taxlabels:
            cmds.append(('TAXLABELS', ' '.join(tlabels.values())))

        mrows = []
        for taxon, dists in matrix.items():
            row = [tlabels[taxon].ljust(maxlen)]
            row.extend(['?' if v is None else str(v) for v in dists.values()])
            mrows.append(' '.join(row))
        cmds.append(('MATRIX', ''.join('\n' + row for row in mrows) + '\n'))
        return cls.from_commands(cmds, nexus=nexus, TITLE=TITLE, LINK=LINK, ID=ID, comment=comment)
