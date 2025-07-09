"""
From the spec:

    The eight [sic! It's nine!] primary public blocks are TAXA, CHARACTERS, UNALIGNED, DISTANCES,
    SETS, ASSUMPTIONS, CODONS, TREES, and NOTES.
"""
from .base import Block  # noqa: F401
from .assumptions import Assumptions  # noqa: F401
from .characters import Characters, Data  # noqa: F401
from .codons import Codons  # noqa: F401
from .distances import Distances  # noqa: F401
from .notes import Notes  # noqa: F401
from .sets import Sets  # noqa: F401
from .taxa import Taxa  # noqa: F401
from .trees import Trees  # noqa: F401
from .unaligned import Unaligned  # noqa: F401
