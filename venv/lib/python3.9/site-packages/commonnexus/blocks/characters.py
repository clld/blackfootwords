import types
import typing
import warnings
import functools
import collections

from .base import Block, Payload
from commonnexus.util import log_or_raise
from commonnexus.tokenizer import (
    iter_words_and_punctuation, Token, iter_delimited, iter_lines, BOOLEAN, word_after_equals, Word,
)
from .taxa import Taxlabels

if typing.TYPE_CHECKING:  # pragma: no cover
    from commonnexus import Nexus

# A state in a CHARACTERS matrix may be missing, gapped, a state symbol or uncertain/polymorphic
# states.
State = typing.Union[None, str, typing.Set[str], typing.Tuple[str]]
StateMatrix = typing.OrderedDict[str, typing.OrderedDict[str, State]]

GAP = '\uFFFD'  # REPLACEMENT CHARACTER used to replace an [...] unrepresentable character
#: Some - but not all - punctuation is invalid as (special) state symbol.
INVALID_SYMBOLS = "()[]{}/\\,;:=*'\"*`<>^"


def duplicate_charlabel(label, cmd, nexus):
    if nexus and nexus.cfg.strict:  # pragma: no cover
        raise ValueError('character names must be unique!')
    else:
        warnings.warn(
            'Duplicate character name "{}" in {} command'.format(label, cmd))


class Eliminate(Payload):
    """
    This command allows specification of a list of characters that are to be excluded from
    consideration. Programs are expected to ignore ELIMINATEd characters completely during reading.
    In avoiding allocation of memory to store character information, the programs can save a
    considerable amount of computer memory. (This subcommand is similar to ZAP in version 3.1.1
    of PAUP.) For example,

    .. code-block::

        ELIMINATE 4-100;

    tells the program to skip over characters 4 through 100 in reading the matrix. Character-set
    names are not allowed in the character list. This command does not affect character numbers.

    .. warning:: The ``ELIMINATE`` command is currently not supported in `commonnexus`.
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        if nexus is not None and not nexus.cfg.ignore_unsupported:
            raise NotImplementedError('The ELIMINATE command is not supported')


class Dimensions(Payload):
    """
    The DIMENSIONS command specifies the number of characters. The number following NCHAR
    is the number of characters in the data matrix. The NEXUS standard does not impose limits on the
    number of characters; a limit may be imposed by particular computer programs.

    It is strongly advised that new taxa not be defined in a CHARACTERS block, for the reasons
    discussed in the description of the DATA block. If new taxa are to be defined, this must be
    indicated by the NEWTAXA subcommand, specifying that new taxa are to be defined (this allows
    the computer program to prepare for creation of new taxa). NEWTAXA, if present, must appear
    before the NTAX subcommand. The NTAX subcommand, indicating the number of taxa in the MATRIX
    command in the block, is optional, unless NEWTAXA is specified, in which case it is required.

    :ivar bool newtaxa:
    :ivar typing.Optional[int] ntax:
    :ivar int nchar:
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.newtaxa = False
        self.ntax = None
        self.char = None
        words = iter_words_and_punctuation(self._tokens, nexus=nexus)
        while 1:
            try:
                word = next(words)
                subcommand = None
                if isinstance(word, str):
                    subcommand = word.upper()
                if subcommand == 'NEWTAXA':
                    self.newtaxa = True
                elif subcommand == 'NTAX':
                    n = next(words)
                    assert n.text == '='
                    self.ntax = int(next(words))
                elif subcommand == 'NCHAR':
                    n = next(words)
                    assert n.text == '='
                    self.nchar = int(next(words))
            except StopIteration:
                break
        self.check()

    def check(self):
        assert self.nchar and ((not self.newtaxa) or self.ntax)


class Format(Payload):
    """
    The FORMAT command specifies the format of the data MATRIX. This is a crucial command because
    misinterpretation of the format of the data matrix could lead to anything from incorrect results
    to spectacular crashes. The DATATYPE subcommand must appear first in the command.

    The RESPECTCASE subcommand must appear before the MISSING, GAP, SYMBOLS, and MATCHCHAR
    subcommands.

    The following are possible formatting subcommands.

    1. DATATYPE = {STANDARD | DNA | RNA | NUCLEOTIDE | PROTEIN | CONTINUOUS}.
       This subcommand specifies the class of data. If present, it must be the first subcommand
       in the FORMAT command. Standard data consist of any general sort of discrete character data,
       and this class is typically used for morphological data, restriction site data, and so on.
       DNA, RNA, NUCLEOTIDE, and PROTEIN designate molecular sequence data. Meristic morphometric
       data and other information with continuous values can be housed in matrices of
       DATATYPE=CONTINUOUS. These DATATYPES are described in detail, with examples, at the end of
       the description of the CHARACTERS block.

       .. warning::

        ``DATATYPE=CONTINUOUS`` is currently not supported in `commonnexus`.
        Some programs accept (or expect) datatypes beyond the ones defined in the NEXUS spec;
        e.g. MrBayes has ``DATATYPE=RESTRICTION`` and Beauti may create "NEXUS" files with
        ``DATATYPE=BINARY``. `commonnexus` does not accept these non-standard datatypes and raises
        an exception when trying to read the MATRIX. Thus, to make "NEXUS" files with
        non-standard datatypes readable for `commonnexus`, substituting ``DATATYPE=STANDARD`` is
        typically the right thing to do.

    2. RESPECTCASE. By default, information in a MATRIX may be entered in uppercase, lowercase, or
       a mixture of uppercase and lowercase. If RESPECTCASE is requested, case is considered
       significant in SYMBOLS, MISSING, GAP, and MATCHCHAR subcommands and in subsequent references
       to states. For example, if RESPECTCASE is invoked, then SYMBOLS="A a B b" designates four
       states whose symbols are A, a, B, and b, which can then each be used in the MATRIX command
       and elsewhere. If RESPECTCASE is not invoked, then A and a are considered homonymous state
       symbols. This subcommand must appear before the SYMBOLS subcommand. This subcommand is not
       applicable to DATATYPE = DNA, RNA, NUCLEOTIDE, PROTEIN, and CONTINUOUS.
    3. MISSING. This subcommand declares the symbol that designates missing data.
       The default is "?". For example, MISSING=X defines an X to represent missing
       data. Whitespace is illegal as a missing data symbol, as are the :data:`INVALID_SYMBOLS`
    4. GAP. This subcommand declares the symbol that designates a data gap (e.g., base absent in
       DNA sequence because of deletion or an inapplicable character in morphological data). There
       is no default gap symbol; a gap symbol must be defined by the GAP subcommand before any gaps
       can be entered into the matrix. For example, GAP=- defines a hyphen to represent a gap.
       Whitespace is illegal as a gap symbol, as are the :data:`INVALID_SYMBOLS`
    5. SYMBOLS. This subcommand specifies the symbols and their order for character states used in
       the file (including in the MATRIX command). For example, SYMBOLS="0 1 2 3 4 5 6 7" designates
       numbers 0 through 7 as acceptable symbols in a matrix. The SYMBOLS subcommand is not allowed
       for DATATYPE=CONTINUOUS. The default symbols list differs from one DATATYPE to another, as
       described under state symbol in the Appendix. Whitespace is not needed between elements:
       SYMBOLS="012" is equivalent to SYMBOLS="0 1 2". For STANDARD DATATYPES, a SYMBOLS subcommand
       will replace the default symbols list of "0 1". For DNA, RNA, NUCLEOTIDE, and PROTEIN
       DATATYPES, a SYMBOLS subcommand will not replace the default symbols list but will add
       character-state symbols to the SYMBOLS list. The NEXUS standard does not define the position
       of these additional symbols within the SYMBOLS list. (These additional symbols will be
       inserted at the beginning of the SYMBOLS list in PAUP and at the end in MacClade. MacClade
       will accept additional symbols for PROTEIN but not DNA, RNA, and NUCLEOTIDE matrices.)

       .. warning::

            While the specification requires the content of the SYMBOLS subcommand to be enclosed in
            doublequotes, `commonnexus` also allows unquoted content; i.e. `SYMBOLS=01` is treated
            as equivalent to `SYMBOLS="01"`.

    6. EQUATE. This subcommand allows one to define symbols to represent one matrix entry. For
       example, EQUATE="E=(012)" means that each occurrence of E in the MATRIX command will be
       interpreted as meaning states 0, 1, and 2. The equate symbols cannot be any of the
       :data:`INVALID_SYMBOLS` or any or the currently defined MISSING, GAP, MATCHCHAR, or state
       SYMBOLS. Case is significant in equate symbols. That is, MISSING=? EQUATE="E=(012)e=?" means
       that E will be interpreted as 0, 1, and 2 and e will be interpreted as missing data.
    7. MATCHCHAR. This subcommand defines a matching character symbol. If this subcommand is
       included, then a matching character symbol in the MATRIX indicates that the states are
       equivalent to the states possessed by the first taxon listed in the matrix for that
       character. In the following matrix, the sequence for taxon 2 is GACTTTC:

       .. code-block::

            BEGIN DATA;
                DIMENSIONS NCHAR = 7;
                FORMAT DATATYPE=DNA MATCHCHAR=.;
                MATRIX
                    taxon_l GACCTTA
                    taxon_2 ...T..C
                    taxon_3 ..T.C..;
            END;

       Whitespace is illegal as a matching character symbol, as are the :data:`INVALID_SYMBOLS`

       .. warning::

            `commonnexus` uses `"."` as default MATCHCHAR. So if `"."` is used as a regular state
            symbol, the NEXUS must be read using the `no_default_matchchar` config option.

    8. [NO]LABELS. This subcommand declares whether taxon or character labels are to appear on the
       left side of the matrix. By default, they should appear. If NOLABELS is used, then no labels
       appear, but then all currently defined taxa must be included in the MATRIX in the order in
       which they were originally defined.
    9. TRANSPOSE. This subcommand indicates that the MATRIX is in transposed format, with each row
       of the matrix representing the information from one character and each column representing
       the information from one taxon. The following is an example of a TRANSPOSEd MATRIX:

       .. code-block::

            MATRIX
                character_1 101101
                character_2 011100
                character_3 011110;

    10. INTERLEAVE. This subcommand indicates that the MATRIX is in interleaved format, i.e., it is
        broken up into sections. If the data are not transposed, then each section contains the
        information for some of the characters for all taxa. For example, the first section might
        contain data for characters 1-50 for all taxa, the second section contains data for
        characters 51-100, etc. Taxa in each section must occur in the same order. This format is
        especially useful for molecular sequence data, where the number of characters can be large.
        A small interleaved matrix follows:

        .. code-block::

            MATRIX
                taxon_1 ACCTCGGC
                taxon_2 ACCTCGGC
                taxon_3 ACGTCGCT
                taxon_4 ACGTCGCT
                taxon_1 TTAACGA
                taxon_2 TTAACCA
                taxon_3 CTCACCA
                taxon_4 TTCACCA

        The interleaved sections need not all be of the same length. In an interleaved matrix,
        newline characters are significant: they indicate that the next character information
        encountered applies to a different taxon (for nontransposed matrices).
    11. ITEMS. Each entry in the matrix gives information about a character's condition
        in a taxon. The ITEMS subcommand indicates what items of information are listed
        at each entry of the matrix. With discrete character data, the entry typically consists
        of the states observed in the taxon (either the single state observed or several states
        if the taxon is polymorphic or of uncertain state). This can be specified by the state-
        ment ITEMS=STATES, but because it is the default and the only option allowed by
        most current programs for discrete data, an ITEMS statement is usually unnecessary.
        For continuous data, however, the wealth of alternatives (average, median, variance,
        minimum, maximum, sample size)t often requires an explicit ITEMS statement to in-
        dicate what information is represented in each data matrix entry. Some ITEMS (such
        as VARIANCE) would be appropriate to only some DATATYPES; other ITEMS such as
        SAMPLESIZE and STATES would be appropriate to most or all DATATYPES. If more
        than one item is indicated, parentheses must be used to surround the list of items,
        e.g., ITEMS=(AVERAGE VARIANCE); otherwise the parentheses are unnecessary,
        e.g., ITEMS=AVERAGE. More information about ITEMS options can be found in the
        discussion of the different DATATYPES under MATRIX; information specifically about
        the STATES option is given under STATESFORMAT.

       .. warning::

            Settings other than ``ITEMS=STATES`` are currently not supported in `commonnexus`.

    12. STATESFORMAT. The entry in a matrix usually lists (for discrete data) or may list
        (for continuous data) the states observed in the taxon. The STATESFORMAT subcommand
        specifies what information is conveyed in that list of STATES. In most current programs for
        discrete data, when a taxon is polymorphic the entry of the matrix lists only what distinct
        states were observed, without any indication of the number or frequency of individuals
        sampled with each of the states. Thus, if all individuals sampled within the taxon have
        state A, the matrix entry would be A, whereas if some have state A and others have state B,
        the entry would be (AB), which corresponds to the option STATESFORMAT=STATESPRESENT.
        Because it is the default for discrete data, this statement is typically unnecessary with
        current programs. The other STATESFORMAT options can be illustrated with an example, in
        which two individuals of a taxon were observed to have state A and three were observed to
        have state B. When STATESFORMAT=INDIVIDUALS, the state of each of the individuals (or other
        appropriate sampling subunit) is listed exhaustively, (A A B B B); when STATESFORMAT=COUNT,
        the number of individuals with each observed state is indicated, e.g., (A:2 B:3); when
        STATESFORMAT=FREQUENCY, the frequencies of various observed states are indicated, e.g.,
        (A:0.40 B:0.60). The STATESFORMAT command may also be used for continuous data, for which
        the default is STATESFORMAT=INDIVIDUALS.

        .. warning::

            Only the default setting ``STATESFORMAT=STATESPRESENT`` is currently supported in
            `commonnexus`.

    13. [NO]TOKENS. This subcommand specifies whether data matrix entries are single symbols or
        whether they can be tokens. If TOKENS, then the data values must be full NEXUS tokens,
        separated by whitespace or punctuation as appropriate, as in the following example:

        .. code-block::

            BEGIN CHARACTERS;
                DIMENSIONS NCHAR= 3 ;
                CHARSTATELABELS 1 hair/absent
                    present, 2 color/red blue,
                    3 size/small big;
                FORMAT TOKENS;
                MATRIX
                    taxon_1 absent red big
                    taxon_2 absent blue small
                    taxon_3 present blue small ;
            END;

        TOKENS is the default (and the only allowed option) for DATATYPE=CONTINUOUS; NOTOKENS is
        the default for all other DATATYPES. TOKENS is not allowed for DATATYPES DNA, RNA, and
        NUCLEOTIDE. If TOKENS is invoked, the standard three-letter amino acid abbreviations can be
        used with DATATYPE=PROTEIN and defined state names can be used for DATATYPE=STANDARD.

        .. warning:: ``TOKENS`` is currently not supported in `commonnexus`.

    :ivar str datatype:
    :ivar bool respectcase:
    :ivar str missing:
    :ivar typing.Optional[str] gap:
    :ivar typing.List[str] symbols:
    :ivar typing.Dict[str, str] equate:
    :ivar typing.Optional[str] matchchar:
    :ivar typing.Optional[bool] labels:
    :ivar bool transpose:
    :ivar bool interleave:
    :ivar typing.List[str] items:
    :ivar typing.Optional[str] statesformat:
    :ivar typing.Optional[bool] tokens:

    .. note::

        It's typically not necessary to access the attributes of a ``Format`` instance from user
        code. Instead, the information is accessed when reading the matrix data in
        :meth:`Characters.get_matrix`.
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.datatype = None
        self.respectcase = False
        self.missing = '?'
        self.gap = None
        self.symbols = ['0', '1']  # The default for DATATYPE=STANDARD
        self.equate = {}
        self.matchchar = None if nexus and nexus.cfg.no_default_matchchar else '.'
        self.labels = None
        self.transpose = False
        self.interleave = False
        self.items = []
        self.statesformat = None
        self.tokens = None
        self.explicit_symbols = False

        if tokens is None:
            return

        words = iter_words_and_punctuation(self._tokens, nexus=nexus)
        after_equals = functools.partial(word_after_equals, words)

        subcommand = None
        subcommands_set = set()
        while 1:
            try:
                word = next(words)
                if isinstance(word, str):
                    subcommand = word.upper()
                elif isinstance(word, Token) and word.text == '=':
                    if subcommand in ['RESPECTCASE', 'TRANSPOSE', 'INTERLEAVE', 'LABELS', 'TOKENS']:
                        # Some NEXUS variants set boolean subcommands always with "=no|yes"
                        word = next(words).lower()
                        if subcommand == 'LABELS' and word == 'left':
                            word = 'yes'
                        setattr(self, subcommand.lower(), BOOLEAN[word])
                        subcommands_set.add(subcommand)
                    elif subcommand:  # pragma: no cover
                        raise ValueError(subcommand)

                if subcommand in ['DATATYPE', 'MISSING', 'MATCHCHAR', 'GAP', 'STATESFORMAT']:
                    setattr(self, subcommand.lower(), after_equals())
                    if subcommand == 'DATATYPE' and self.datatype.upper() != 'STANDARD':
                        self.symbols = []
                elif subcommand in ['RESPECTCASE', 'TRANSPOSE', 'INTERLEAVE']:
                    if subcommand not in subcommands_set:
                        setattr(self, subcommand.lower(), True)
                elif subcommand in ['NOLABELS', 'LABELS', 'NOTOKENS', 'TOKENS']:
                    setattr(self, subcommand.replace('NO', '').lower(), 'NO' not in subcommand)
                elif subcommand == 'SYMBOLS':
                    self.explicit_symbols = True
                    self.symbols = []
                    next_token_text = after_equals()
                    if not next_token_text.startswith('"'):
                        self.symbols = list(next_token_text)
                    else:
                        for w in iter_delimited(next_token_text, words):
                            if isinstance(w, str):
                                self.symbols.extend(list(w))
                            else:
                                assert w.text in '+-'
                                self.symbols.append(w.text)
                elif subcommand == 'EQUATE':
                    key, e, bracket = None, False, None
                    for t in iter_delimited(after_equals(), words):
                        if isinstance(t, Token):
                            if t.text == '=':
                                assert key
                                e = True
                                bracket = None
                            else:
                                bracket = t.text
                        elif isinstance(t, str):
                            if key:
                                assert e
                                if bracket is None:
                                    assert len(t) == 1
                                    self.equate[key] = t
                                elif bracket == '(':
                                    self.equate[key] = tuple(t)
                                elif bracket == '{':
                                    self.equate[key] = set(t)
                                else:  # pragma: no cover
                                    raise ValueError(
                                        'Invalid punctuation in EQUATE content: {}'.format(bracket))
                                key, e = None, False
                            else:
                                key = t
                elif subcommand == 'ITEMS':
                    for w in iter_delimited(
                            after_equals(), words, delimiter='()', allow_single_word=True):
                        assert isinstance(w, str)
                        self.items.append(w)
            except StopIteration:
                break
        if self.datatype:
            self.datatype = self.datatype.upper()
            assert self.datatype in {
                'STANDARD', 'DNA', 'RNA', 'NUCLEOTIDE', 'PROTEIN', 'CONTINUOUS'}
            if self.datatype == 'CONTINUOUS' and not self.nexus.cfg.ignore_unsupported:
                raise NotImplementedError('DATATYPE=CONTINUOUS is not supported!')
        self.items = [i.upper() for i in self.items]
        assert all(
            i in 'MIN MAX MEDIAN AVERAGE VARIANCE STDERROR SAMPLESIZE STATES'.split()
            for i in self.items)
        if not self.items:
            self.items = ['STATES']
        if self.items != ['STATES']:
            raise NotImplementedError('Only ITEMS=STATES is supported!')
        if self.statesformat:
            self.statesformat = self.statesformat.upper()
            assert self.statesformat in {'STATESPRESENT', 'INDIVIDUALS', 'COUNT', 'FREQUENCY'}
        else:
            self.statesformat = 'STATESPRESENT'
        if self.statesformat != 'STATESPRESENT':
            raise NotImplementedError(
                'STATESFORMATs other than STATESPRESENT are not supported')
        for attr in ['missing', 'gap', 'matchchar']:
            c = getattr(self, attr)
            if c:
                assert len(c) == 1 and c not in INVALID_SYMBOLS
        if self.tokens:
            raise NotImplementedError('TOKENS is not supported')

        if self.datatype in {'DNA', 'RNA', 'NUCLEOTIDE'}:
            T = 'U' if self.datatype == 'RNA' else 'T'
            self.symbols.extend(list('ACG' + T))
            self.equate.update(
                R=set('AG'),
                Y=set('C' + T),
                M=set('AC'),
                K=set('G' + T),
                S=set('CG'),
                W=set('A' + T),
                H=set('AC' + T),
                B=set('CG' + T),
                V=set('ACG'),
                D=set('AG' + T),
                N=set('ACG' + T),
                X=set('ACG' + T),
            )
            if self.datatype == 'NUCLEOTIDE':
                self.equate.update(U='T')
        elif self.datatype == 'PROTEIN':
            self.symbols.extend(list('ACDEFGHIKLMNPQRSTVWY*'))
            self.equate.update(B=set('DN'), Z=set('EQ'))

        if not self.respectcase:
            self.equate = {k.upper(): v for k, v in self.equate.items()}

        invalid_equate = \
            list(INVALID_SYMBOLS) + self.symbols + \
            [self.missing or '', self.gap or '', self.matchchar or '']
        assert not any(c in invalid_equate for c in self.equate)


class Charstatelabels(Payload):
    """
    This command allows specification of both the names of the characters and the names of the
    states. This command was developed as an alternative to the older commands CHARLABELS and
    STATELABELS. For example,

    .. code-block::

        CHARSTATELABELS
            1 eye_color/red blue green,
            3 head_shape/round square,
            5 pronotum_size/small medium large

    A forward slash (/) separates the character name and the state names, with a comma separating
    the information for different characters. If no state names are to be specified, the slash may
    be omitted; if no character names are to be specified, the slash must be included, but no token
    needs to be included between the character number and the slash. If state x is the last state
    to be named, then subsequent states need not be named, but states 1 through x must be. If no
    name is to be applied to a state, enter a single underscore for its name. Character and state
    names are single NEXUS words. Character names must not correspond to another character name or
    number; thus, 1 is not a valid name for the second character listed. State names cannot be
    applied if DATATYPE=CONTINUOUS.

    :ivar typing.List[types.SimpleNamespace] characters:

    .. code-block:: python

        >>> cmd = Charstatelabels('1 eye_color/red blue green, 3 head_shape/round square')
        >>> cmd.characters[0].name
        'eye_color'
        >>> cmd.characters[0].states
        ['red', 'blue', 'green']

    .. warning::

        In strict mode (see :class:`commonnexus.nexus.Config`) duplicate character names will raise
        a ``ValueError``, otherwise a ``UserWarning`` will be emitted. While a matrix with duplicate
        character names can still be read, it will typically **not** be as expected, because only
        the values for the last character for a given name will be present.
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.characters = []
        names = set()
        words = iter_words_and_punctuation(self._tokens, nexus=nexus)
        num, name, states, in_states, comma = None, None, [], False, False

        while 1:
            try:
                w = next(words)
                if num is None:
                    num = int(w)
                    continue
                if isinstance(w, Token) and w.text == ',':
                    comma = True  # We want to be able to detect trailing commas!
                    if name and name in names:
                        duplicate_charlabel(name, 'CHARSTATELABELS', nexus)
                    names.add(name)
                    self.characters.append(
                        types.SimpleNamespace(number=num, name=name, states=states))
                    num, name, states, in_states = None, None, [], False
                    continue
                if in_states:
                    states.append(w)
                    continue
                if isinstance(w, Token) and w.text == '/':
                    in_states = True
                    continue
                if name:
                    raise ValueError(
                        'Illegal token in charstatelabel: "{}{}"'.format(name, w))
                name = w
            except StopIteration:
                break
        if num:
            if name and name in names:
                duplicate_charlabel(name, 'CHARSTATELABELS', nexus)
            self.characters.append(types.SimpleNamespace(number=num, name=name, states=states))
        elif comma:  # There was a comma, but no new label.
            warnings.warn('Trailing comma in CHARSTATELABELS command')


class Charlabels(Payload):
    """
    This command allows specification of names of characters:

    .. code-block::

        CHARLABELS
            flange microsculpture
            body_length
            hind_angles #_spines
            spine_size _ _ head_size
            pubescent_intervals head_color
            clypeal_margin;

    Character labels are listed consecutively. If character x is the last character to be named,
    then subsequent characters need not be named, but characters 1 through x need to be. If no name
    is to be applied to a character, a single underscore can be used for its name. Character names
    are single NEXUS words. They must not correspond to another character name or number; thus, 1
    is not a valid name for the second character listed. The command should be used only for
    nontransposed matrices (in transposed matrices, the character labels are defined in the MATRIX
    command). We recommend that programs abandon this command in place of the more flexible
    CHARSTATELABELS command when writing NEXUS files, although programs should continue to read
    CHARLABELS because many existing NEXUS files use CHARLABELS.

    :ivar typing.List[types.SimpleNamespace] characters:
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.characters = []
        names = set()
        for i, w in enumerate(iter_words_and_punctuation(self._tokens, nexus=nexus)):
            assert isinstance(w, str)
            if w and w in names:
                duplicate_charlabel(w, 'CHARLABELS', nexus)
            names.add(w)
            self.characters.append(types.SimpleNamespace(number=i + 1, name=w, states=[]))


class Statelabels(Payload):
    """
    This command allows specification of the names of states:

    .. code-block::

        STATELABELS
            1 absent present,
            2 isodiametric transverse,
            3 '4.5-6.2mm' '6.3-7.0mm' '7.7-11.0mm' '>12.0mm',
            4 rounded subangulate angulate,
            10 0 '1-4' '6-9' '7-9' '8-9' 7 8 9,
            11 black rufous metallic flavous,
            12 straight concave,

    State labels need not be specified for all characters. A comma must separate state labels for
    each character. State labels are listed consecutively within a character. If state x is the
    last state to be named, then subsequent states need not be named, but states 1 through x must
    be. If no name is to be applied to a state, enter a single underscore for its name. State
    names are single NEXUS words. This command is not valid for DATATYPE=CONTINUOUS.
    We recommend that programs abandon this command in place of the more flexible
    CHARSTATELABELS command when writing NEXUS files, although programs should continue to read
    STATELABELS because many existing NEXUS files use STATELABELS.

    :ivar typing.List[types.SimpleNamespace] characters:
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.characters = []

        words = iter_words_and_punctuation(self._tokens, nexus=nexus)
        num, states = None, []

        while 1:
            try:
                w = next(words)
                if num is None:
                    num = int(w)
                    continue
                if isinstance(w, Token) and w.text == ',':
                    self.characters.append(
                        types.SimpleNamespace(number=num, name=None, states=states))
                    num, states = None, []
                    continue
                assert isinstance(w, str)
                states.append(w)
            except StopIteration:
                break
        if num and states:
            self.characters.append(types.SimpleNamespace(number=num, name=None, states=states))


class Matrix(Payload):
    """
    In its standard format, the MATRIX command contains a sequence of taxon names and state
    information for that taxon. The MATRIX itself is of the form

    .. code-block::

        MATRIX
            taxon-name entry entry... entry
            taxon-name entry entry... entry
            taxon-name entry entry... entry;

    Each entry in the matrix is the information about a particular character for a particular taxon.
    For example, it might be the assignment of state 0 to taxon 1 for character 1. Thus, the entry
    would consist of one state symbol, 0. If the taxon were polymorphic, the entry would consist
    of multiple state symbols, e.g. (0 1), indicating the taxon has both states 0 and 1. More
    details about the nature of each entry of the matrix are given under ITEMS and under each
    DATATYPE. Each entry needs to be enclosed in parentheses or braces whenever more than one state
    symbol is given, e.g. (01) with standard data and the default NOTOKENS option, or if the
    information is conveyed by more than one NEXUS token, e.g., (0:100) or (2.3 4.5 6.7). Otherwise,
    the parentheses or braces are optional. No whitespace is needed between entries in the matrix
    unless the TOKENS subcommand of the FORMAT command is invoked or implied and parentheses or
    braces do not surround an entry.
    Taxa need not be in the same order as in the TAXA block, and the matrix need not contain all
    taxa. For interleaved matrices, all sections must have the same taxa in the same order.
    Examples of matrices of different DATATYPES are described below.

    1. For STANDARD data, each entry of the matrix consists of a single state-set. Under the
       defaults (ITEMS=STATES and STATESFORMAT=STATESPRESENT), each entry of the matrix consists of
       a single state-set; if there are multiple states, then the entry must be enclosed in
       parentheses (indicating polymorphism) or braces (indicating uncertainty in state). For
       example, in the following matrix,

       .. code-block::

            BEGIN CHARACTERS;
                DIMENSIONS NCHAR=9;
                FORMAT SYMBOLS="-+x";
                MATRIX
                    taxon_1 (-+){-+}+---+--
                    taxon_2 +x-++--+x
                    taxon_3 -++++--+x;
            END;

       taxon_1 is polymorphic for the first character and has either state - or state + for the
       second character. If STATESFORMAT=COUNT or FREQUENCY, then each entry must be enclosed in
       parentheses because more than one token is required to convey information for even one state:

       .. code-block::

            BEGIN CHARACTERS;
                DIMENSIONS NCHAR=3;
                FORMAT STATESFORMAT=FREQUENCY SYMBOLS = "012";
                MATRIX
                    taxon_1 (0:0.251:0.75) (0:0.31:0.7) (0:0.51:0.32:0.2)
                    taxon_2 (0:0.41:0.6) (0:0.81:0.2) (1:0.152:0.85)
                    taxon_3 (0:0.01:1.0) (0:0.551:0.45) (0:0.11:0.9);
            END;

    2. For DNA, RNA, NUCLEOTIDE, and PROTEIN data, each entry of the matrix consists of one or more
       state symbols describing the state(s) at one site in a molecular sequence. If
       STATESFORMAT=STATESPRESENT and if an entry represents a single state, then it is represented
       as a single state symbol (or if DATATYPE=PROTEIN and TOKENS, as a three-letter amino acid
       name). If an entry represents multiple states, then it must be enclosed in parentheses
       (indicating polymorphism) or braces (indicating uncertainty in state). Following is a matrix
       of DATATYPE=DNA:

       .. code-block::

            BEGIN CHARACTERS;
                DIMENSIONS NCHAR=12;
                FORMAT DATATYPE = DNA;
                MATRIX
                    taxon_1 ACCATGGTACGT
                    taxon_2 TCCATGCTACCC
                    taxon_3 TCCATGGAACCC;
            END;

    3. For CONTINUOUS data, each entry in the matrix must be enclosed by parentheses if more than
       one item is specified in the ITEMS subcommand. Parentheses must also be used whenever
       multiple tokens are needed for an entry in the matrix. If an entry consists of a single
       token (eg., 0.231), it may be written without parentheses but must then be separated from
       other entries by whitespace.

       .. code-block::

            MATRIX
                A 0.453 1.43 78.6
                B 0.34 1.02 55.7
                C 0.22 1.79 69.1;

       A matrix entry can include average, minimum, maximum, variance, standard error, sample size,
       and a listing of states observed in the taxon, as specified in the ITEMS subcommand. The
       sample size, if included, must be in the form of an integer; the other numbers can be either
       in English decimal (e.g., 0.00452) or in exponential form (e.g., 4.52E-3). The information
       listed for each taxon for a continuous character is specified in the ITEMS subcommand of the
       FORMAT command. For example, if the matrix contains only information about the minimum and
       maximum value for each taxon, the ITEMS subcommand would be ITEMS=(MIN MAX) and a small
       matrix might look something like this:

       .. code-block::

            MATRIX
                taxon_1 (0.21 0.45) (0.34 0.36)
                taxon_2 (0.13 0.22) (0.45 0.55);

       If the ITEMS include the raw measurements (states), e.g., to list a sample of measurements
       from individuals, then the other items must precede the listing of states. There is no
       restriction on the number of elements in the listing of states. This example has only one
       continuous character:

       .. code-block::

            FORMAT DATATYPE=CONTINUOUS ITEMS=(AVERAGE STATES) STATESFORMAT=INDIVIDUALS;
            MATRIX
                taxon_1 (1.2 2.1 1.6 0.8 1.8 0.3 0.6)
                taxon_2 (1.6 2.2 1.7 1.0 2.0 1.6 1.9 0.8);

       in which the first value is the sample average and the subsequent values comprise the sample
       of observed states. Possible ITEMS to be included are MIN (minimum), MAX (maximum), AVERAGE
       (sample average), VARIANCE (sample variance), STDERROR (standard error), MEDIAN
       (sample median), SAMPLESIZE, and STATES. The manner of presentations of states can be
       indicated using the STATESFORMAT command. The default ITEMS for continuous data is AVERAGE.

    .. note::

        Since reading the matrix data only makes sense if information from other commands - in
        particular :class:`FORMAT <Format>` - is considered, the ``Matrix`` object does not have
        any attributes for data access. Instead, the matrix data can be read via
        :meth:`Characters.get_matrix`.
    """


class Characters(Block):
    """
    A CHARACTERS block defines characters and includes character data.

    Taxa are usually not defined in a CHARACTERS block; if they are not, the CHARACTERS block must
    be preceded by a block that defines taxon labels and ordering (e.g., TAXA).

    Syntax of the CHARACTERS block is as follows:

    .. rst-class:: nexus

        | BEGIN CHARACTERS;
        |   :class:`DIMENSIONS <Dimensions>` [NEWTAXA NTAX=num-taxa] NCHAR=num-characters;
        |   [:class:`FORMAT <Format>`
        |       [DATATYPE = { STANDARD| DNA | RNA | NUCLEOTIDE | PROTEIN | CONTINUOUS} ]
        |       [RESPECTCASE]
        |       [MISSING=symbol]
        |       [GAP=symbol]
        |       [SYMBOLS="symbol [symbol...]"]
        |       [EQUATE="symbol = entry [symbol = entry... ] " ]
        |       [MATCHCHAR= symbol ]
        |       [[NO]LABELS]
        |       [TRANSPOSE]
        |       [INTERLEAVE]
        |       [ITEMS=([MIN] [MAX] [MEDIAN] [AVERAGE] [VARIANCE] [STDERROR] [SAMPLESIZE] [STATES])]
        |       [STATESFORMAT= {STATESPRESENT | INDIVIDUALS | COUNT | FREQUENCY}]
        |       [[NO]TOKENS]
        |   ;]
        |   [:class:`ELIMINATE <Eliminate>` character-set;]
        |   [:class:`TAXLABELS <commonnexus.blocks.taxa.Taxlabels>` taxon-name [taxon-name ...];]
        |   [:class:`CHARSTATELABELS <Charstatelabels>`
        |       character-number [character-name] [/state-name [state-name...]]
        |       [, character-number [character-name] [/state-name [state-name...]]...]
        |   ;]
        |   [:class:`CHARLABELS  <Charlabels>` character-name [character-name...];]
        |   [:class:`STATELABELS <Statelabels>`
        |       character-number [state-name [state-name ...]]
        |       [, character-number [state-name [state-name...]]...]
        |   ;]
        |   :class:`MATRIX <Matrix>` data-matrix;
        | END;

    :class:`DIMENSIONS <Dimensions>`, :class:`FORMAT <Format>`, and :class:`ELIMINATE <Eliminate>`
    must all precede :class:`CHARLABELS <Charlabels>`, :class:`CHARSTATELABELS <Charstatelabels>`,
    :class:`STATELABELS <Statelabels>`, and :class:`MATRIX <Matrix>`.
    :class:`DIMENSIONS <Dimensions>` must precede :class:`ELIMINATE <Eliminate>`.
    Only one of each command is allowed per block.
    """
    __commands__ = [
        Dimensions, Format, Eliminate, Taxlabels, Charstatelabels, Charlabels, Statelabels, Matrix]

    def is_binary(self) -> bool:
        """
        :return: Whether the matrix in the block is binary, i.e. codes items as presence/absence \
        using symbols "01".
        """
        return not bool(self.FORMAT) or (self.FORMAT.symbols == ['0', '1'])

    def get_matrix(self, labeled_states: bool = False) -> StateMatrix:
        """
        :param labeled_states: Flag signaling whether state symbols should be translated to state \
        labels (if available).
        :return: The values of the matrix, read according to FORMAT. The matrix is returned as \
        ordered `dict`, mapping taxon labels (if available, else numbers) to ordered `dict`s \
        mapping character labels (if available, else numbers) to state values. State values are \
        either atomic values (of type `str`) or `tuple`s (indicating polymorphism) or `set`s \
        (indicating uncertainty) of atomic values. Atomic values may be `None` (indicating missing \
        data), the special string `GAP` (indicating gaps) or state symbols or labels (if available \
        and explicitly requested via `labeled_states=True`). State symbols are returned using the \
        case given in FORMAT SYMBOLS, i.e. if a RESPECTCASE directive is missing and \
        FORMAT SYMBOLS="ABC", a value "a" in the matrix will be returned as "A".
        """
        format = Format(None) if 'FORMAT' not in self.commands else self.FORMAT

        # Determine dimensions and labels:
        ntax, taxlabels = self.get_taxlabels(format)
        nchar = self.DIMENSIONS.nchar
        charlabels, statelabels = self.get_charstatelabels(nchar, format)
        if format.transpose and (not format.interleave) and (format.labels != False) and (not ntax):
            raise ValueError("Can't read transposed matrix without NTAX.")  # pragma: no cover
        if format.datatype == 'CONTINUOUS':  # pragma: no cover
            raise NotImplementedError("Can't read a matrix of datatype CONTINUOUS")

        # We read the matrix data in an agnostic way, ignoring whether it's transposed or not, as
        # ordered dictionary mapping row labels (or numbers) to lists of entries.
        res = collections.OrderedDict()
        label, entries = None, []
        ncols, nrows = ntax if format.transpose else nchar, nchar if format.transpose else ntax

        for i, line in enumerate(
                list(iter_lines(self.MATRIX._tokens)) if format.interleave else
                [self.MATRIX._tokens],
                start=1):
            words = iter_words_and_punctuation(
                line, allow_punctuation_in_word='+-', nexus=self.nexus)
            while 1:
                try:
                    t = next(words)
                    if (format.labels is not False) and label is None:
                        assert isinstance(t, str)
                        label = t
                        continue
                    if isinstance(t, Token):
                        if t.text == '(':
                            w = next(words)
                            symbols = ''
                            while isinstance(w, str) or (w.text in format.symbols) \
                                    or (w.text == ","):
                                if isinstance(w, str) or w.text != ',':
                                    symbols += getattr(w, 'text', w)
                                w = next(words)
                            assert w.text == ')', "Expected )"
                            entries.append(tuple(symbols))
                        elif t.text == '{':
                            w = next(words)
                            vals = set()
                            while isinstance(w, str) or (w.text in format.symbols) \
                                    or (w.text == format.gap) or (w.text == ","):
                                if isinstance(w, str) or w.text != ',':
                                    vals |= set(getattr(w, 'text', w))
                                w = next(words)
                            assert w.text == '}', "Expected }"
                            entries.append(vals)
                        elif t.text in format.symbols:  # pragma: no cover
                            entries.append(t.text)
                        else:  # pragma: no cover
                            raise ValueError('Unexpected punctuation in matrix')
                    else:
                        entries.extend(list(t))  # We split a word into a list of symbols.
                    if not format.interleave and (len(entries) == ncols):
                        res[label or (len(res) + 1)] = entries
                        label, entries = None, []
                except StopIteration:
                    break
            if format.interleave:
                key = label or (i % nrows or nrows)
                if key not in res:
                    res[key] = []
                res[key].extend(entries)
                label, entries = None, []

        cols = ncols or len(list(res.values())[0])
        assert all(len(states) == cols for states in res.values()), "Incomplete matrix read!"
        if not taxlabels:
            assert not format.transpose
            taxlabels = {i + 1: key for i, key in enumerate(res)}

        def apply_to_state(func, state, *args, **kw):
            # We have to do a bit of mapping and renaming, which always needs to deal with the
            # three different types of state.
            if isinstance(state, str):
                return func(state, *args, **kw)
            if isinstance(state, tuple):
                return tuple(func(s, *args, **kw) for s in state)
            if isinstance(state, set):
                return set(func(s, *args, **kw) for s in state)
            raise ValueError(state)  # pragma: no cover

        lax_symbols = not format.explicit_symbols and format.datatype in {None, 'STANDARD'} \
            and not (self.nexus and self.nexus.cfg.strict)

        def replace_symbol(s, i, r):
            if (format.respectcase and s == format.missing) or \
                    (not format.respectcase and (s.upper() == format.missing.upper())):
                return None
            if format.gap:
                if (format.respectcase and s == format.gap) or \
                        (not format.respectcase and (s.upper() == format.gap.upper())):
                    return GAP
            if format.matchchar:  # match entries from first row!
                if (format.respectcase and s == format.matchchar) or \
                        (not format.respectcase and (s.upper() == format.matchchar.upper())):
                    assert r
                    return r[i]
            if s not in format.symbols:
                s = s.lower() if s.isupper() else s.upper()

            if not lax_symbols:
                assert s in format.symbols, '{} {}'.format(s, format.symbols)
            return s

        def resolve_symbols(s, i, r):
            def resolve(c, i, r):
                c = format.equate.get(c.upper(), c)  # May result in ambiguous or multiple states!
                return apply_to_state(replace_symbol, c, i, r)
            return apply_to_state(resolve, s, i, r)

        firstrow = None
        for i, l in enumerate(res):
            res[l] = [resolve_symbols(s, i, firstrow) for i, s in enumerate(res[l])]
            if i == 0:
                # We need the fully resolved entries of the first row around to resolve MATCHCHARs.
                firstrow = res[l]

        # Create the final result, an OrderedDict mapping taxa labels (or numbers) to OrderedDicts
        # mapping character labels or numbers to state symbols or labels.
        matrix = collections.OrderedDict()
        if not format.transpose:
            tlabels = {str(k) for k in res.keys()}
            valid_taxa = {str(k) for k in taxlabels}.union(taxlabels.values())
            if not tlabels.issubset(valid_taxa):
                if self.nexus and self.nexus.cfg.strict:  # pragma: no cover
                    raise ValueError('Found undeclared taxa in characters matrix')
                else:
                    warnings.warn('Dropping undeclared taxa from characters matrix.')

        for tnum, tlabel in sorted(taxlabels.items()):
            if format.transpose:
                # We have to pick the tnum column in each list in res.
                matrix[tlabel] = collections.OrderedDict()
                for cnum, clabel in sorted(charlabels.items()):
                    entries = res[clabel] if clabel in res else res[cnum]
                    matrix[tlabel][clabel] = entries[tnum - 1]
            else:
                key = tlabel if tlabel in res else (tnum if tnum in res else str(tnum))
                if key in res:
                    # Non-transposed matrices may not have data for each taxon!
                    entries = res[key]
                    matrix[tlabel] = collections.OrderedDict(
                        [(charlabels[i], s) for i, s in enumerate(entries, start=1)])
        if labeled_states:
            for entries in matrix.values():
                for char in entries:
                    if char in statelabels:
                        if entries[char] not in {None, GAP}:
                            entries[char] = apply_to_state(
                                lambda s: statelabels[char].get(s) or s, entries[char])
        return matrix

    def get_taxlabels(self, format):
        if self.TAXLABELS:
            taxlabels = self.TAXLABELS.labels
            ntax = self.DIMENSIONS.ntax
        elif 'TAXA' in self.linked_blocks:
            taxlabels = self.linked_blocks['TAXA'].TAXLABELS.labels
            ntax = self.linked_blocks['TAXA'].DIMENSIONS.ntax
        elif self.nexus.TAXA:
            taxlabels = self.nexus.TAXA.TAXLABELS.labels
            ntax = self.nexus.TAXA.DIMENSIONS.ntax
        else:
            ntax, taxlabels = None, {}

        if format.interleave and format.labels is False and not format.transpose:
            # If the matrix has no row labels and is not transposed, we need the number of taxa to
            # compute the size of the interleaved blocks.
            assert ntax
            taxlabels = taxlabels or {i + 1: str(i + 1) for i in range(ntax)}
        return ntax, taxlabels

    def get_charstatelabels(self, nchar=None, format=None):
        nchar = nchar or self.DIMENSIONS.nchar
        charlabels = {i + 1: str(i + 1) for i in range(nchar)}
        statelabels = {}

        if self.CHARSTATELABELS:
            charlabels = {
                int(c.number): c.name or str(c.number) for c in self.CHARSTATELABELS.characters}
            statelabels = {
                c.number: c.states for c in self.CHARSTATELABELS.characters}
        elif self.CHARLABELS:
            charlabels = {
                int(c.number): c.name or str(c.number) for c in self.CHARLABELS.characters}
        if self.STATELABELS:
            statelabels = {c.number: c.states for c in self.STATELABELS.characters}

        format = format or self.FORMAT or Format(None)
        if statelabels:
            statelabels = {charlabels[cnum]: states for cnum, states in statelabels.items()}
            for clabel in statelabels:
                states = statelabels[clabel]
                labeled = collections.OrderedDict()
                if format:
                    for i, symbol in enumerate(format.symbols):
                        if i < len(states) and states[i] != '_':
                            labeled[symbol] = states[i]
                statelabels[clabel] = labeled
        else:
            statelabels = {}
        assert len(charlabels) == nchar
        return charlabels, statelabels

    def validate(self, log=None):
        res = super().validate(log)
        if 'TAXLABELS' in self.commands and not self.DIMENSIONS.newtaxa:
            return log_or_raise(
                'TAXLABELS may only be defined in {} block if NEWTAXA is specified.'.format(
                    self.name),
                log=log)
        return res

    @classmethod
    def from_data(cls,
                  matrix: StateMatrix,
                  taxlabels: bool = False,
                  statelabels: typing.Optional[typing.Dict[str, typing.Dict[str, str]]] = None,
                  datatype: str = 'STANDARD',
                  missing: str = '?',
                  gap: str = '-',
                  comment: typing.Optional[str] = None,
                  nexus: typing.Optional["Nexus"] = None,
                  TITLE: typing.Optional[str] = None,
                  ID: typing.Optional[str] = None,
                  LINK: typing.Optional[typing.Union[str, typing.Tuple[str, str]]] = None) \
            -> 'Characters':
        """
        Instantiate a CHARACTERS or DATA block from a metrix.

        This functionality can be used to normalize the NEXUS formatting of CHARACTERS matrices:

        .. code-block:: python

            >>> nex = Nexus('''#NEXUS
            ... BEGIN TAXA;
            ... DIMENSIONS NTAX=3;
            ... TAXLABELS t1 t2 t3;
            ... END;
            ... BEGIN CHARACTERS;
            ... DIMENSIONS NCHAR=3;
            ... FORMAT TRANSPOSE NOLABELS;
            ... MATRIX 100 010 001;
            ... END;''')
            >>> matrix = nex.CHARACTERS.get_matrix()
            >>> nex.replace_block(nex.CHARACTERS, Characters.from_data(matrix))
            >>> print(nex)
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

        :param matrix: A matrix as returned by :meth:`Characters.get_matrix()`, with unlabeled \
        states. I.e. `None` is used to mark missing values, and `GAP` to mark gapped values. These \
        special states will be converted to the symbols passed as `missing` and `gap` upon writing.
        :param taxlabels: If `True`, include a TAXLABELS command rather than relying on a TAXA \
        block being present.
        :param datatype:
        :param missing:
        :param gap:
        :param nexus: An optional Nexus instance to lookup global config options.
        """
        if datatype != 'STANDARD':  # pragma: no cover
            raise NotImplementedError('Only DATATYPE=STANDARD is supported for writing CHARACTERS')

        symbols, rows, charlabels, maxlen, tlabels = set(), [], None, 0, {}
        for taxon in matrix:  # We compute maximum taxon label length for pretty printing.
            tlabels[taxon] = Word(taxon).as_nexus_string()
            maxlen = max([maxlen, len(tlabels[taxon])])

        symbol = lambda c: missing if c is None else (gap if c == GAP else c)  # noqa: E731

        for taxon, entries in matrix.items():
            if not charlabels:
                charlabels = collections.OrderedDict(
                    [(str(i + 1), c) for i, c in enumerate(entries)])
            row = []
            for entry in entries.values():
                if entry:
                    symbols |= set(entry)
                if isinstance(entry, tuple):  # polymorphism -> ()
                    row.append('({})'.format(''.join(symbol(c) for c in entry)))
                elif isinstance(entry, set):  # uncertainty -> {}
                    row.append('{{{}}}'.format(''.join(sorted(symbol(c) for c in entry))))
                else:
                    row.append(symbol(entry))
            rows.append('\n{} {}'.format(tlabels[taxon].ljust(maxlen), ''.join(row)))

        symbols = ''.join(sorted([s for s in symbols if s not in [None, GAP]]))
        if missing in symbols or (gap in symbols):
            raise ValueError('MISSING or GAP markers must be distinct from "{}"'.format(symbols))
        respectcase = any(c.isupper() for c in symbols) and any(c.islower() for c in symbols)

        dimensions = 'NCHAR={}'.format(len(list(matrix.values())[0]))
        if taxlabels:
            dimensions = 'NEWTAXA NTAX={} {}'.format(len(tlabels), dimensions)
        cmds = [
            ('DIMENSIONS', dimensions),
            ('FORMAT', 'DATATYPE=STANDARD {}MISSING={} GAP={} SYMBOLS="{}"'.format(
                'RESPECTCASE ' if respectcase else '', missing, gap, symbols)),
        ]
        statelabels = statelabels or {}
        if any(k != v for k, v in charlabels.items()):
            cmds.append((
                'CHARSTATELABELS',
                ', '.join('\n    {} {}{}'.format(
                    n,
                    Word(l).as_nexus_string(),
                    '/' + ' '.join(Word(ll).as_nexus_string() for ll in statelabels[l].values())
                    if statelabels.get(l) else '',
                ) for n, l in charlabels.items())))
        if taxlabels:
            cmds.append(('TAXLABELS', ' '.join(tlabels.values())))
        cmds.append(('MATRIX', ''.join(rows) + '\n'))
        return cls.from_commands(cmds, nexus=nexus, TITLE=TITLE, ID=ID, LINK=LINK, comment=comment)


class Options(Payload):
    """
    The GAPMODE subcommand of the OPTIONS command of the ASSUMPTIONS block was originally
    housed in an OPTIONS command in the DATA block.

    :ivar typing.Optional[str] gapmode: `missing` or `newstate`.
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.gapmode = None

        words = iter_words_and_punctuation(self._tokens, nexus=nexus)

        while 1:
            try:
                word = next(words)
                if isinstance(word, str) and word.upper() == 'GAPMODE':
                    self.gapmode = word_after_equals(words).lower()
            except StopIteration:
                break
        assert self.gapmode in {None, 'missing', 'newstate'}


class Data(Characters):
    """
    This block is equivalent to a CHARACTERS block in which the NEWTAXA subcommand is included in
    the DIMENSIONS command. That is, the DATA block is a CHARACTERS block that includes not only
    the definition of characters but also the definition of taxa.

    .. note::

        The GAPMODE subcommand of the OPTIONS command of the ASSUMPTIONS block was originally
        housed in an :class:`OPTIONS <Options>` command in the DATA block.
    """
    __commands__ = [
        Dimensions, Format, Options,
        Eliminate, Taxlabels, Charstatelabels, Charlabels, Statelabels, Matrix]
