import typing
import pathlib
import itertools
import collections
import dataclasses

from .tokenizer import TokenType, iter_tokens, get_name
from .util import log_or_raise
from commonnexus.command import Command
from commonnexus.blocks import Block

__all__ = ['Config', 'Nexus']

NEXUS = '#NEXUS'


@dataclasses.dataclass
class Config:
    """
    The global behaviour of a :class:`Nexus` instance can be configured.
    The available configuration options are set and accessed from an instance of `Config`.
    """
    #: Specifies whether "-", aka ASCII hyphen-minus, is considered punctuation or not.
    hyphenminus_is_text: bool = True
    #: Specifies whether "*", aka asterisk, is considered punctuation or not.
    asterisk_is_text: bool = True
    #: Specifies whether Newick nodes for TREEs are constructed by parsing the Newick string or
    #: from the Nexus tokens. The latter is slightly faster but will bypass some input validation.
    validate_newick: bool = False
    #: Specifies whether unsupported NEXUS commands/options are ignored or raise an error. Note \
    #: that the effect of this option may only set in when a block or command is accessed.
    ignore_unsupported: bool = True
    #: Specifies the text encoding of a NEXUS file.
    encoding: str = 'utf8'
    #: The NEXUS spec does not explicitly state a default value for the MATCHCHAR directive in the
    #: FORMAT command of a CHARACTERS block. `commonnexus` - in agreement with many NEXUS files
    #: encountered "in the wild" - assumes a default of ".". To force no default value for
    #: MATCHCHAR, e.g. because matrix data uses "." as regular state symbol, set
    #: `no_default_matchchar` to `True`.
    no_default_matchchar: bool = False
    #: Sometimes the NEXUS spec is not followed entirely by files found in the wild. If somewhat
    #: lax interpretation does not lead to ambiguities, that's what commonnexus does. To force
    #: stricter adherence to the spec, set `strict` to `True`.
    strict: bool = False


class Nexus(list):
    """
    A NEXUS object implemented as list of commands with methods to read and write blocks.

    From the spec:

        The tokens in a NEXUS file are organized into commands, which are in turn organized into
        blocks.

    This is reflected in the ``Nexus`` object. The ``Nexus`` object is just a ``list`` of
    :class:`Commands <Command>`, and has a property :meth:`Nexus.blocks` giving access to
    commands grouped by block:

    .. code-block::

        >>> nex = Nexus('#NEXUS BEGIN myblock; mycmd a b c; END;')
        >>> nex[0].__class__
        <class 'commonnexus.nexus.Command'>
        >>> len(nex.blocks['MYBLOCK'])
        1

    .. note::

        NEXUS is for the most part case-insensitive. `commonnexus` reflects this by giving all
        blocks and commands uppercase names. Thus, even if a command or block has a lowercase or
        mixed-case name in the file, the corresponding ``Command`` or ``Block`` object must be
        addressed using the uppercase name.
    """
    def __init__(self,
                 s: typing.Optional[typing.Union[typing.Iterable, typing.List[Command]]] = None,
                 block_implementations: typing.Optional[typing.Dict[str, Block]] = None,
                 config: typing.Optional[Config] = None,
                 **kw):
        """
        :param s: The NEXUS content.
        :param block_implementations: Custom implementations for non-public blocks.
        :param config: Configuration.
        :param kw: If no :class:`Config` object is passed as `config`, keyword parameters will be \
        interpreted as configuration options. Thus,

        .. code-block:: python

            >>> nex = Nexus(encoding='latin')

        is a shortcut for

        .. code-block:: python

            >>> nex = Nexus(config=Config(encoding='latin'))
        """
        self.cfg = config or Config(**kw)
        self.trailing_whitespace = []
        self.leading = []
        self.block_implementations = {}
        for cls in Block.__subclasses__():
            self.block_implementations[cls.__name__.upper()] = cls
            for scls in cls.__subclasses__():
                self.block_implementations.setdefault(scls.__name__.upper(), scls)

        self.block_implementations.update(block_implementations or {})
        s = s or NEXUS

        if isinstance(s, str):
            s = iter(s)

        if not isinstance(s, list):
            nexus, commands, tokens = False, [], []
            for token in itertools.dropwhile(
                    lambda t: t.type == TokenType.WHITESPACE, iter_tokens(s)):
                if not nexus:
                    assert token.type == TokenType.WORD and token.text.upper() == NEXUS, \
                        "No #NEXUS token found."
                    nexus = True
                else:
                    tokens.append(token)
                    if token.is_semicolon:
                        commands.append(Command(tuple(tokens)))
                        tokens = []
            if commands:
                self.trailing_whitespace = tokens
            else:
                self.leading = tokens
            s = commands
        list.__init__(self, s)

    @classmethod
    def from_file(cls,
                  p: typing.Union[str, pathlib.Path],
                  config: typing.Optional[Config] = None,
                  **kw) -> 'Nexus':
        """
        Instantiate a `Nexus` object from the contents of a NEXUS file.

        :param p: Path of the file.
        :param config: An optional configuration object.
        :param kw: Configuration options, if no `Config` object is passed in.
        :return: A `Nexus` instance.
        """
        config = config or Config(**kw)
        p = pathlib.Path(p)
        not_utf8 = False
        with p.open(encoding=config.encoding) as f:
            try:
                return cls(itertools.chain.from_iterable(f), config=config)
            except UnicodeDecodeError:
                not_utf8 = config.encoding == 'utf8'
        if not_utf8:
            # We don't want to do a lot of guessing, but if the default encoding was tried and
            # didn't work, we try with the old-time favourite "latin1":
            config.encoding = 'latin1'
            with p.open(encoding=config.encoding) as f:
                return cls(itertools.chain.from_iterable(f), config=config)

    @classmethod
    def from_blocks(cls, *blocks):
        res = cls()
        for block in blocks:
            res.append_block(block)
        return res

    @property
    def blocks(self) -> typing.Dict[str, typing.List[Block]]:
        """
        A `dict` mapping uppercase block names to lists of instances of these blocks ordered as they
        appear in the NEXUS content.

        For a shortcut to access blocks which are known to appear just once in the NEXUS content,
        see :meth:`Nexus.__getattribute__`.
        """
        res = collections.defaultdict(list)
        for block in self.iter_blocks():
            res[block.name].append(block)
        return res

    def __getattribute__(self, name):
        """
        NEXUS does not make any prescriptions regarding how many blocks with the same name may
        exist in a file. Thus, the primary way to access blocks is by looking up the list of blocks
        for a given name in :meth:`Nexus.blocks`. If it can be assumed that just one block for a
        name exists, or only the first block with that name is of interest, this block can also be
        accessed as `Nexus.<BLOCK_NAME>`, i.e. using the uppercase block name as attribute of the
        `Nexus` instance.

        .. code-block:: python

            >>> nex = Nexus('#NEXUS begin block; cmd; end;')
            >>> nex.BLOCK.name
            'BLOCK'
            >>> len(nex.BLOCK.commands)
            1
        """
        if name.isupper():
            try:
                return self.blocks[name][0]
            except IndexError:
                return None
        return list.__getattribute__(self, name)

    def __str__(self):
        """
        The string representation of a `Nexus` object is just its NEXUS content.

        .. code-block:: python

            >>> nex = Nexus()
            >>> nex.append_block(Block.from_commands([]))
            >>> print(nex)
            #NEXUS
            BEGIN BLOCK;
            END;
        """
        return NEXUS \
            + ''.join(str(t) for t in self.leading) \
            + ''.join(''.join(str(t) for t in cmd) for cmd in self) \
            + ''.join(str(t) for t in self.trailing_whitespace)

    def to_file(self, p: typing.Union[str, pathlib.Path]):
        """
        Write the NEXUS content of a `Nexus` object to a file.
        """
        p = pathlib.Path(p)
        text = str(self)
        text += '\n' if not text.endswith('\n') else ''
        p.write_text(text, encoding=self.cfg.encoding)

    def iter_comments(self):
        yield from (t for t in self.leading if t.type == TokenType.COMMENT)
        for cmd in self:
            yield from (t for t in cmd if t.type == TokenType.COMMENT)
        yield from (t for t in self.trailing_whitespace if t.type == TokenType.COMMENT)

    @property
    def comments(self) -> typing.List[str]:
        """
        Comments may appear anywhere in a NEXUS file. Thus, they are the only kind of tokens not
        really grouped into a command.

        While comments **in** commands can also be accessed from the command, comments preceding
        any command (and all others) can accessed via this property.

        .. code-block:: python

            >>> nex = Nexus("#nexus [created by commonnexus] begin block; cmd [does nothing]; end;")
            >>> nex.BLOCK.CMD.comments
            ['does nothing']
            >>> nex.comments[0]
            'created by commonnexus'
        """
        return [t.text for t in self.iter_comments()]

    def iter_blocks(self):
        block = None
        for command in itertools.dropwhile(lambda c: not c.is_beginblock, self):
            if command.is_endblock:
                block.append(command)
                # Look up a suitable Block implementation.
                name = get_name(block[0].iter_payload_tokens())
                yield self.block_implementations.get(name, Block)(self, block)
                block = None
            elif command.is_beginblock:
                block = [command]
            elif block is not None:
                block.append(command)

    def validate(self, log=None):
        valid = True
        if any(t.type not in {TokenType.WHITESPACE, TokenType.COMMENT} for t in self.leading):
            log_or_raise('Invalid token in preamble', log=log)
        for block in self.iter_blocks():
            #
            # FIXME: we can do a lot of validation here! If block.__commands__ is a list, there is
            # some fixed order between commands.
            # If Payload.__multivalued__ == False, only one command instance is allowed, ...
            #
            valid = valid and block.validate(log=log)
        if any(t.type not in {TokenType.WHITESPACE, TokenType.COMMENT}
               for t in self.trailing_whitespace):
            log_or_raise('Invalid token in text after the last command', log=log)
        return valid

    def get_numbers(self, object_name, items):
        """
        Determine object numbers suitable for inclusion in a set spec.
        """
        if object_name == 'TAXON':
            return [str(i + 1) for i, tax in enumerate(self.taxa)
                    if (tax in items) or (str(i + 1) in items)]
        if object_name == 'CHARACTER':
            charlabels, statelabels = self.characters.get_charstatelabels()
            return [str(i) for i, label in charlabels.items()
                    if (label in items) or (str(i) in items)]
        if object_name == 'TREE':
            return [str(i + 1) for i, tree in enumerate(self.TREES.trees)
                    if (tree.name in items) or (str(i + 1) in items)]
        raise NotImplementedError(object_name)  # pragma: no cover

    def resolve_set_spec(self, object_name, spec, chars=None):
        """
        Resolve a set spec to a list of included items, specified by label or number.

        :param object_name:
        :param spec:
        :return:
        """
        def numbers(maxn):
            res = []
            start, r = None, False
            for token in spec:
                if not start:
                    start = token
                else:
                    if token == '-':
                        r = True
                    else:
                        if r:
                            res.extend(list(
                                range(int(start), int(token if token != '.' else maxn) + 1)))
                            r, start = False, None
                        else:
                            res.append(int(start))
                            start = token
            if start:
                res.append(int(start))
            return res

        object_name = object_name.upper()
        assert object_name in ['TAXON', 'CHARACTER', 'STATE', 'TREE']
        n, labels = None, None
        if object_name == 'TAXON':
            if self.TAXA:
                # FIXME: What if there's more than one TAXA block?
                n = self.TAXA.DIMENSIONS.ntax
                labels = self.TAXA.TAXLABELS.labels
            elif self.CHARACTERS and self.CHARACTERS.DIMENSIONS.newtaxa:
                n = self.CHARACTERS.DIMENSIONS.ntax
                if self.CHARACTERS.TAXLABELS:
                    labels = self.CHARACTERS.TAXLABELS.labels

        if object_name == 'CHARACTER':
            block = self.CHARACTERS or self.DATA
            if block:
                labels, _ = block.get_charstatelabels()
                n = len(labels)

        if object_name == 'STATE':
            chars = chars or []  # Labeled states make only sense in relation to characters.
            block = self.CHARACTERS or self.DATA
            if block:
                _, slabels = block.get_charstatelabels()
                res = collections.defaultdict(list)
                # need to transpose
                for char, states in slabels.items():
                    if char in chars:
                        res[char] = [
                            label or state for state, label in states.items() if state in spec]
                return res
            return  # pragma: no cover

        if object_name == 'TREE':
            labels = {i + 1: tree.name for i, tree in enumerate(self.TREES.trees)}

        if not labels:
            assert n
            labels = {i + 1: str(i + 1) for i in range(n)}
        return [labels[n] for n in numbers(n)]

    def remove_block(self, block: Block):
        for cmd in block:
            self.remove(cmd)

    def append_block(self, block: Block):
        self.extend(block)

    def prepend_block(self, block: Block):
        for cmd in reversed(block):
            self.insert(0, cmd)

    def replace_block(self,
                      old: Block,
                      new: typing.Union[Block, typing.List[typing.Tuple[str, str]]]):
        bname = old.name
        for i, cmd in enumerate(self):
            if cmd is old[0]:
                break
        else:
            raise ValueError('Block not found')  # pragma: no cover

        for cmd in old:
            self.remove(cmd)

        if isinstance(new, Block):
            new.nexus = self
            for cmd in reversed(new):
                self.insert(i, cmd)
        else:
            self.insert(i, Command.from_name_and_payload('END'))
            for n, payload in reversed(new):
                self.insert(i, Command.from_name_and_payload(n, payload))
            self.insert(i, Command.from_name_and_payload('BEGIN', bname))

    def append_command(self, block, name, payload=None):
        self.insert(
            self.index(block[-1]),
            Command.from_name_and_payload(name, payload))

    # Shortcuts:
    @property
    def characters(self) -> typing.Union[Block, None]:
        """
        Shortcut to get around the DATA/CHARACTERS ambiguity.

        I.e. if one is interested in the characters matrix of a NEXUS file no matter whether this
        is included in a DATA or CHARACTERS block, ``Nexus.characters.get_matrix()`` can be used
        rather than ``(Nexus.DATA or NEXUS.CHARACTERS).get_matrix()``.

        :return: The first DATA or CHARACTERS block.
        """
        assert not (self.DATA and self.CHARACTERS)
        return self.DATA or self.CHARACTERS

    @property
    def taxa(self) -> typing.Optional[typing.List[str]]:
        """
        Shortcut to retrieve the list of taxa a NEXUS file provides data on.

        :return: The list of taxa labels used in a NEXUS file.

        .. note::

            There are various ways to encode taxa labels in a NEXUS file. This method looks up
            different places ordered by explicitness, i.e.

            1. A TAXLABELS command in a TAXA block.
            2. A TAXLABELS command in a DATA or CHARACTERS block.
            3. Taxa labels given implicitly as labels in a MATRIX command.
            4. A TAXLABELS command in a DISTANCES block.
            5. Taxa labels given implicitly as labels in a DISTANCES.MATRIX command.
            6. Taxa labels given as mappings in the TRANSLATE command of a TREES block.
            7. Taxa labels given implicitly as node names in the Newick representation of a tree in
               a TREE command in a TREES block.

        .. warning::

            Taxa descriptions in NEXUS may be inconsistent, e.g. a NEXUS file might contain a
            TAXA block, but introduce new taxa via NEWTAXA/TAXLABELS in a CHARACTERS block.
            `commonnexus` does not make an effort to check for consistency.
        """
        if self.TAXA and len(self.blocks['TAXA']) == 1:
            return list(self.TAXA.TAXLABELS.labels.values())
        if self.characters:
            return list(self.characters.get_matrix())
        if self.DISTANCES:
            return list(self.DISTANCES.get_matrix())
        if self.TREES:
            if self.TREES.TRANSLATE:
                return list(self.TREES.TRANSLATE.mapping.values())
            return [node.name for node in self.TREES.TREE.newick.walk() if node.name]
