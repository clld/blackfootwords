from .base import Block


class Unaligned(Block):
    """
    .. warning::

        `commonnexus` doesn't provide any functionality - other than parsing as generic commands -
        for ``UNALIGNED`` blocks yet.

    The UNALIGNED block includes data that are not aligned. Its primary intent is to house
    unaligned DNA, RNA, NUCLEOTIDE, and PROTEIN sequence data. Taxa are usually not defined in an
    UNALIGNED block; if not, this block must be preceded by a block that defines taxon labels and
    ordering (e.g., TAXA).
    Syntax of the UNALIGNED block is as follows:

    .. rst-class:: nexus

        | BEGIN UNALIGNED;
        |   [DIMENSIONS NEWTAXA NTAX=number-of-taxa;]
        |   [FORMAT
        |     [DATATYPE = { STANDARD | DNA | RNA | NUCLEOTIDE | PROTEIN}]
        |     [RESPECTCASE]
        |     [MISSING=symbol]
        |     [SYMBOLS="symbol [symbol...]"]
        |     [EQUATE = "symbol=entry [symbol=entry...]"]
        |     [[NO]LABELS]
        |   ;]
        |   [TAXLABELS taxon-name [taxon-name...];]
        |   MATRIX data-matrix;
        | END;

    Commands must appear in the order listed. Only one of each command is allowed per block.
    The DIMENSIONS command should only be included if new taxa are being defined in this block,
    which is discouraged (see discussion under DATA block). The format for the DIMENSIONS command
    is as in the CHARACTERS block, except NCHAR is not allowed.
    Subcommands of the FORMAT command are described in the CHARACTERS block. The TAXLABELS command
    serves to define taxa and is only allowed if the NEWTAXA token is included in the DIMENSIONS
    statement. It follows the same form as described in the TAXA block.
    Here is an example of an UNALIGNED block

    .. code-block::

        BEGIN UNALIGNED;
            FORMAT DATATYPE=DNA;
            MATRIX
                taxon_1 ACTAGGACTAGATCAAGTT,
                taxon_2 ACCAGGACTAGCGGATCAAG,
                taxon_3 ACCAGGACTAGATCAAG,
                taxon_4 AGCCAGGACTAGTTC,
                taxon_5 ATCAGGACTAGATCAAGTTC;
        END;

    A comma must be placed at the end of each sequence (except the last, which requires a
    semicolon). Each sequence can occupy more than one line.
    """
