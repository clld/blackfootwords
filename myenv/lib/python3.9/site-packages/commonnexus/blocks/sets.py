from .base import Block, Payload


class Charset(Payload):
    """
    This command specifies and names a set of characters; this name can then be used in subsequent
    CHARSET definitions or wherever a character-set is required. The VECTOR format consists of 0's
    and 1's: a 1 indicates that the character is to be included in the CHARSET; whitespace is not
    necessary between 0's and l's. The name of a CHARSET cannot be equivalent to a character name
    or character number.

    **Predefined character-sets**:

    - The character-set ``CONSTANT`` is predefined for all DATATYPES; it specifies all invariant
      characters.
    - The character-set ``REMAINDER`` is predefined for all DATATYPES; it specifies all characters
      not previously referenced in the command.
    - The character-set ``GAPPED`` is predefined for all DATATYPES; it specifies all characters
      with a gap for at least one taxon.

    There are four additional predefined character-sets for characters of DATATYPE=DNA, RNA, and
    NUCLEOTIDE:

    1. ``POS1`` - All characters defined by current CODONPOSSET as first positions.
    2. ``POS2`` - All characters defined by current CODONPOSSET as second positions.
    3. ``POS3`` - All characters defined by current CODONPOSSET as third positions.
    4. ``NONCODING`` - All characters defined by current CODONPOSSET as non-protein-coding sites.
    """
    # syntax: a b c-g x-.


class Stateset(Payload):
    """
    This command allows one to name a set of states; it is not currently supported by any program.
    It is not available for DATATYPE=CONTINUOUS. For STANDARD format, the state-set is described by
    a list of state symbols, except that it should not be enclosed in parentheses or braces. Any
    current state-set symbols are valid in the state-set description.
    The following STATESET

    .. code-block::

        STATESET theSet = 2 3 4 5;

    defines the set composed of states 2, 3, 4, and 5.

    The VECTOR format consists of 0's and 1's: a 1 indicates that the state is to be included in
    the STATESET; whitespace is not necessary between 0's and l's. For example, the state-set

    .. code-block::

        STATESET theSet (VECTOR) =1001000;

    designates theSet to be the set containing first and fourth states.

    .. warning::

        `commonnexus` can read NEXUS containing this command, but will not resolve references to
        state-sets anywhere.
    """


class Changeset(Payload):
    """
    This command allows naming of a set of state changes; it is not currently supported by any
    program. It is not available for DATATYPE=CONTINUOUS. The description of the CHANGESET consists
    of pairs of state-sets joined by an operator. State-sets that consist of more than one token
    must be contained in parentheses. There are two allowed operators: ``->`` and ``<->``
    (``<-`` is **not** allowed). These operators can best be explained by example.

    .. code-block::

        CHANGESET changes1 = (1 2 3) -> (4 6) ;
        CHANGESET changes2 = 1 <-> 4 ;
        CHANGESET transversions = (A G) <-> (C T) ;

    The first CHANGESET represents any change from 1 to 4, 1 to 6, 2 to 4, 2 to 6, 3 to 4, or 3 to
    6, and the second set represents changes from 1 to 4 and 4 to 1. The CHANGESET "transversions"
    defines the set of all changes between purines and pyrimidines as transversions.
    """


class Taxset(Payload):
    """
    This command defines a set of taxa. A TAXSET name can be used in subsequent TAXSET definitions
    or wherever a taxon-set is required. The name of a TAXSET cannot be equivalent to a taxon name
    or taxon number. The taxa to be included are described in a taxon-set. For example, the
    following command

    .. code-block::

        TAXSET beetles=0mma-.;

    defines the TAXSET "beetles" to include all taxa from the taxon Omma to the last defined taxon.
    The VECTOR format consists of 0's and 1's: a 1 indicates that the taxon is to be included in
    the TAXSET; whitespace is not necessary between 0's and 1's.
    """


class Treeset(Payload):
    """
    This command defines a set of trees. A TREESET name can be used in subsequent TREESET
    definitions or wherever a tree-set is required. It is not currently supported by any program.
    It follows the same general format as a TAXSET command.

    .. warning::

        `commonnexus` can read NEXUS containing this command, but will not resolve references to
        tree-sets anywhere.
    """


class Partition(Payload):
    """
    [*]PARTITION commands define partitions of characters, taxa, and trees, respectively.
    The partition divides the objects into several (mutually exclusive) subsets.
    They all follow the same format. There are several formatting options. The VECTOR format
    consists of a list of partition names. By default, the name of each subset is a NEXUS word
    (this is the TOKENS option). The NOTOKENS option is only available in the VECTOR format; this
    allows use of single symbols for the subset names. Each value in a definition in VECTOR format
    must be separated by whitespace if the names are tokens but not if they are NOTOKENS. The
    following two examples are equivalent:

    .. code-block::

        TAXPARTITION populations = 1:1-3 , 2: 4-6 , 3:7 8;
        TAXPARTITION populations (VECTOR NOTOKENS) =11122233;

    The following two examples are equivalent:

    .. code-block::

        TAXPARTITION mypartition= Chiricahua: 1-3, Huachuca: 4-6, Galiuro: 7 8;
        TAXPARTITION mypartition (VECTOR) =
            Chiricahua Chiricahua Chiricahua Huachuca Huachuca Huachuca Galiuro Galiuro;
    """


class Charpartition(Partition):
    pass


class Taxpartition(Partition):
    pass


class Treepartition(Partition):
    pass


class Sets(Block):
    """
    This block stores sets of objects (characters, states, taxa, etc.).

    The general structure of the SETS block is as follows.

    .. rst-class:: nexus

        | BEGIN SETS;
        |     [:class:`CHARSET <Charset>` charset-name [({STANDARD | VECTOR})] = character-set; ]
        |     [:class:`STATESET <Stateset>` stateset-name [({STANDARD | VECTOR})] = state-set;]
        |     [:class:`CHANGESET <Changeset>`
        |         changeset-name=state-set<-> state-set [state-set<-> state-set...];]
        |     [:class:`TAXSET <Taxset>` taxset-name [({ STANDARD | VECTOR})] = taxon-set; ]
        |     [:class:`TREESET <Treeset>` treeset-name [({STANDARD | VECTOR})] = tree-set;]
        |     [:class:`CHARPARTITION <Charpartition>` partition-name
        |         [([{[NO]TOKENS}] [{STANDARD | VECTOR}])]
        |         =subset-name:character-set[, subset-name:character-set ...]
        |     ;]
        |     [:class:`TAXPARTITION <Taxpartition>` partition-name
        |         [([{[No]TOKENS}] [{STANDARD | VECTOR}])]
        |         =subset-name:taxon-set[, subset-name:taxon-set...]
        |     ;]
        |     [:class:`TREEPARTITION <Treepartition>` partition-name
        |         [([{[No]TOKENS}] [{STANDARD | VECTOR}])]
        |         =subset-name: tree-set[, subset-name:tree-set...]
        |     ;]
        | END;

    An example SETS block is

    .. code-block::

        BEGIN SETS;
            CHARSET larval = 1-3 5-8;
            STATESET eyeless = 0;
            STATESET eyed = 1 2 3;
            CHANGESET eyeloss = eyed -> eyeless;
            TAXSET outgroup=l-4;
            TREESET AfrNZVicariance = 3 5 9-12;
            CHARPARTITION bodyparts=head: 1-4 7, body:5 6, legs: 8-10 ;
        END;
    """
    __commands__ = [
        Charset, Stateset, Changeset, Taxset, Treeset, Charpartition, Taxpartition, Treepartition]
