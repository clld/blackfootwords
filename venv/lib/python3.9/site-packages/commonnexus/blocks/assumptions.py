from .base import Block


class Assumptions(Block):
    """
    .. warning::

        `commonnexus` doesn't provide any functionality - other than parsing as generic commands -
        for ``ASSUMPTIONS`` blocks.

        .. code-block:: python

            >>> nex = Nexus('''#NEXUS
            ...     BEGIN ASSUMPTIONS;
            ...         OPTIONS DEFTYPE=ORD;
            ...         USERTYPE my0rd = 4
            ...                 0 1 2 3
            ...                 . 1 2 3
            ...                 1 . 1 2
            ...                 2 1 . 1
            ...                 3 2 1 .;
            ...         USERTYPE myTree (CSTREE) = ((0,1) a,(2,3)b)c;
            ...         TYPESET * mixed=lRREv: 1 3 10, UNORD 5-7;
            ...         WTSET * one = 2 : 1-3 6 11-15, 3: 7 8;
            ...         WTSET two = 2:4 9, 3: 1-3 5;
            ...         EXSET nolarval = 1-9;
            ...         ANCSTATES mixed = 0: 1 3 5-8 11, 1: 2 4 9-15;
            ...     END;''')
            >>> str(nex.ASSUMPTIONS.ANCSTATES)
            'mixed = 0: 1 3 5-8 11, 1: 2 4 9-15'

    The ASSUMPTIONS block houses assumptions about the data or gives general directions as to how
    to treat them (e.g., which characters are to be excluded from consideration). The commands
    currently placed in this block were primarily designed for parsimony analysis. More commands,
    embodying assumptions useful in distance, maximum likelihood, and other sorts of analyses, will
    be developed in the future.
    For example, matrices specifying relative rates of character state change, useful for both
    distance and likelihood analyses, will eventually be included here.
    The general structure of the assumptions block is

    .. rst-class:: nexus

        | BEGIN ASSUMPTIONS;
        |   [OPTIONS [DEFTYPE = type-name]
        |     [POLYTCOUNT= {MINSTEPS | MAXSTEPS}]
        |     [GAPMODE= {MISSING | NEWSTATE}];]
        |     [USERTYPE type-name [ ( {STEPMATRIX | CSTREE} ) ] =UsERTYPE-description; ]
        |   [TYPESET [*] typeset-name [ ({STANDARD | VECTOR} ) ] = TYPESET-definition;]
        |   [WTSET [*] wtset-name [({STANDARD | VECTOR} {TOKENS | NOTOKENS})] = WrSET-defini tion;]
        |   [EXSET [*] exset-name [( {STANDARD | VECTOR} ) ] = character-set; ]
        |   [ANCSTATES [*] ancstates-name [({STANDARD | VECTOR} {[NO]TOKENS})] =
        |     ANCSTATES-definition;]
        | END;

    An example ASSUMPTIONS block follows:

    .. code-block::

        BEGIN ASSUMPTIONS;
            OPTIONS DEFTYPE=ORD;
            USERTYPE my0rd = 4
                0 1 2 3
                . 1 2 3
                1 . 1 2
                2 1 . 1
                3 2 1 .;
            USERTYPE myTree (CSTREE) = ((0,1) a,(2,3)b)c;
            TYPESET * mixed=lRREv: 1 3 10, UNORD 5-7;
            WTSET * one = 2 : 1-3 6 11-15, 3: 7 8;
            WTSET two = 2:4 9, 3: 1-3 5;
            EXSET nolarval = 1-9;
            ANCSTATES mixed = 0: 1 3 5-8 11, 1: 2 4 9-15;
        END;

    **USERTYPES** must be defined before they are referred to in any TYPESET.

    In earlier versions of MacClade and PAUP, TAXSET and CHARSET also appeared in the
    ASSUMPTIONS block. These now appear in the SETS block. There are a number of other commands
    in the ASSUMPTIONS block that also have SET in their name (e.g., WTSET, EXSET), but these
    commands assign values to objects, they do not define sets of objects, and therefore they
    do not belong in the SETS block. (Commands such as WTSET and EXSET are so named for
    historical reasons; although they might ideally be renamed CHARACTERWEIGHTS and
    EXCLUDEDCHARACTERS, doing so would cause existing programs to be incompatible with the file
    format.) We recommend that programs also accept TAXSET and CHARSET commands in the
    ASSUMPTIONS block so that older files can be read. In addition, the GAPMODE subcommand of
    the OPTIONS command of this block was originally housed in an OPTIONS command in the DATA
    block. Because this subcommand dictates how data are to be treated rather than providing
    details about the data themselves, it was moved into the ASSUMPTIONS block.

    **OPTIONS** — This command houses a number of disparate subcommands. They are all of the form
    subcommand=option.

    1. **DEFTYPE**. This subcommand specifies the default character type for parsimony analyses.
       Whenever a character's type is not explicitly stated, its type is taken to be the default
       type. Default DEFTYPE is UNORD (see the Appendix, character trans-
       formation type, for a definition of UNORD).
    2. **POLYTCOUNT**. Setting POLYTCOUNT to MINSTEPS specifies that trees with polytomies are to
       be counted (in parsimony analyses) in such a way that the number of steps for each character
       is the minimum number of steps for that character over any resolution of the polytomy. A
       tree length that is the sum of these minimum numbers of steps may be below the tree length
       of the most-parsimonious dichotomous resolution. Setting POLYTCOUNT to MAXSTEPS specifies
       that trees with polytomies are to be counted in such a way that occurrence of derived states
       on elements of a polytomy are to be counted as independent derivations. Such a tree length
       may be above the tree length of any fully dichotomous resolution. The NEXUS format does not
       specify a default value for POLYTCOUNT; the default value may differ from program to program.
    3. **GAPMODE**. This subcommand specifies how gaps are to be treated. GAPMODE=MISSING specifies
       that gaps are to be treated in the same way as missing data; GAPMODE=NEWSTATE specifies that
       gaps are to be treated as an additional state (for DNA/RNA/NUCLEOTIDE data, as a fifth base).

    **USERTYPE** —This command defines a character transformation type, as used in parsimony
    analysis to designate the cost of changes between states. There are several predefined
    character types (see character transformation type in the Appendix); USERTYPE allows additional
    character types to be created. USERTYPE is an object definition command with the exception that
    an asterisk cannot be used to indicate the default type (default type is stated in the OPTIONS
    command of the ASSUMPTIONS block). The standard defines no limit to the length of the type name,
    although individual programs might impose restrictions.

    STEPMATRIX format is

    .. code-block::

        USERTYPE myMatrix (STEPMATRIX) = n
            s s s s
            . k k k
            k . k k
            k k . k
            k k k .;

    where n is the number of rows and columns in the step matrix, the s's are state symbols, and
    the k's are the cost for going between states. The n can take any value >2. Diagonal elements
    may be listed as periods. If a change is to be prohibited, then one enters an "i" for infinity.
    Typically, the state symbols will be in sequence, but they need not be. The following matrices
    assign values identically:

    .. code-block::

        USERTYPE myMatrix (STEPMATRIX) =4
            0 1 2 3
            . 1 5 1
            1 . 5 1
            5 5 . 5
            1 1 5 . ;
        USERTYPE myMatrix2 (STEPMATRIX) =4
            2 0 3 1
            . 5 5 5
            5 . 1 1
            5 1 . 1
            5 1 1 .;

    The number of steps may be either integers or real numbers. The range of possible values will
    differ from program to program. Versions 3.0-3.04 of MacClade use the format name REALMATRIX
    rather than STEPMATRIX if the matrix contains real numbers. Future programs should treat
    REALMATRIX as a synonym of STEPMATRIX.

    CSTREE format is very similar to the TREE format in a TREES block. That is, character state
    trees are described in the parenthesis notation following the rules given for TREES of taxa.
    Instead of taxon labels, character state symbols are used. Thus,

    .. code-block::

        USERTYPE cstree-name (CSTREE) = [{list-of-subtrees)] [state-symbol]];

    where each subtree has the same format as the overall tree and the subtrees are separated by
    commas.

    **TYPESET** — This command specifies the type assigned to each character as used in parsimony
    analysis. This is a standard object definition command. Any characters not listed in the
    character-set have the default character type. The type names to be used are either the
    predefined ones or those defined in a USERTYPE command. Each value in a definition in VECTOR
    format must be separated by whitespace. The following are equivalent type sets:

    .. code-block::

        TYPESET mytypes = ORD: 1 4 6 , UNORD: 2 3 5 ;
        TYPESET mytypes (VECTOR) = ORD UNORD UNORD ORD UNORD ORD;

    **WTSET** — This command specifies the weights of each character. This is a standard object
    definition command. Any characters not listed in the character-set have weight 1. The weights
    may be either integers or real numbers. The minimum and maximum weight value will differ from
    program to program. Each value in a definition in VECTOR format must be separated by whitespace
    unless the NOTOKENS option is invoked, in which case no whitespace is needed and all weights
    must be integers in the range 0-9. The following are equivalent weight sets:

    .. code-block::

        WTSET mywts = 3 : 1 4 6, 1: 2 3 5;
        WTSET mywts (VECTOR) =3 1 1 3 1 3 ;

    In earlier versions of MacClade, the formatting subcommand REAL was used to indicate that
    real-valued weights were included in the WTSET. This subcommand is no longer in use; programs
    are expected to detect the presence of integral or real-value weights while reading the WTSET
    command.

    **EXSET** — This command specifies which characters are to be excluded from consideration. This
    is a standard object definition command. Any characters not listed in the character-set are
    included. The VECTOR format consists of 0's and l's: a 1 indicates that the character is to be
    excluded; whitespace is not necessary between 0's and l's.
    The following commands are equivalent and serve to exclude characters 5, 6, 7, 8, and 12.

    .. code-block::

        EXSET * toExclude = 5-8 12;
        EXSET * toExclude (VECTOR) = 000011110001;

    **ANCSTATES** — This command allows specification of ancestral states. This is a standard object
    definition command. Any valid state symbol can be used in the description for discrete data, and
    any valid value can be used for continuous data. TOKENS is the default for DATATYPE=CONTINUOUS;
    NOTOKENS is the default for all other DATATYPES. TOKENS is not allowed for DATATYPES DNA, RNA,
    and NUCLEOTIDE. If TOKENS is invoked, the standard three-letter amino acid abbreviations can be
    used with DATATYPE=PROTEIN and defined state names can be used for DATATYPE=STANDARD. NOTOKENS
    is not allowed for DATATYPE=CONTINUOUS. The following commands are equivalent:

    .. code-block::

        ANCSTATES a n c e s t o r = 0 :1-3 5-7 12, 1:4 8-10, 2 : 1 1 ;
        ANCSTATES a n c e s t o r (VECTOR) = 000100011120;
    """
    pass
