"""
Basic building blocks of NEXUS files.
"""
import re
import typing
import functools
import collections

from commonnexus.tokenizer import (
    get_name, iter_tokens, iter_words_and_punctuation, word_after_equals, TokenType, Word,
)
from commonnexus.command import Command

if typing.TYPE_CHECKING:  # pragma: no cover
    from commonnexus import Nexus


class Payload:
    """
    The payload of a Nexus command, i.e. the stuff between command name and final ";".
    """
    __multivalued__ = False

    def __init__(self, tokens, nexus=None):
        self.nexus = nexus
        self._tokens = list(iter_tokens(iter(tokens))) if isinstance(tokens, str) else tokens

    @functools.cached_property
    def comments(self):
        return [t.text for t in self._tokens if t.type == TokenType.COMMENT]

    def format(self, *args, **kw):
        """
        Derived classes may provide functionality to format command data as correct Nexus payload.
        """
        raise NotImplementedError()  # pragma: no cover

    def __str__(self):
        return ''.join(str(t) for t in self._tokens)

    @property
    def lines(self):
        return re.split(r'[\t\r ]*\n[\t\r ]*', str(self))


class Title(Payload):
    """
    Support for Mesquite's mechanism to link blocks.

    https://phylo.bio.ku.edu/slides/lab9-MesquiteAncStatesBisse/09-Mesquite.html#Create_a_tree_file
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.title = next(iter_words_and_punctuation(self._tokens, nexus=nexus)).upper()
        assert isinstance(self.title, str)


class Id(Payload):
    """
    Support for Mesquite's mechanism to link blocks.

    https://phylo.bio.ku.edu/slides/lab9-MesquiteAncStatesBisse/09-Mesquite.html#Create_a_tree_file
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        self.id = next(iter_words_and_punctuation(self._tokens, nexus=nexus))
        assert isinstance(self.id, str)


class Link(Payload):
    """
    Support for Mesquite's mechanism to link blocks.

    https://phylo.bio.ku.edu/slides/lab9-MesquiteAncStatesBisse/09-Mesquite.html#Create_a_tree_file
    """
    def __init__(self, tokens, nexus=None):
        super().__init__(tokens, nexus=nexus)
        words = iter_words_and_punctuation(self._tokens, nexus=nexus)
        self.block = next(words).upper()
        self.title = word_after_equals(words).upper()


class Block(tuple):
    """
    A Block is a list of commands, starting with a BEGIN command and ending with END.

    .. code-block:: python

        >>> print(Block.from_commands([]))
        BEGIN BLOCK;
        END;
        >>> print(Block.from_commands([('CMD', 'A=1')]))
        BEGIN BLOCK;
            CMD A=1;
        END;
    """
    # Custom `Payload` subclasses can be registered for command names:
    __commands__ = {}

    def __new__(cls, nexus, cmds):
        return super().__new__(cls, tuple(cmds))

    def __init__(self, nexus, cmds):
        self.nexus = nexus

    def __str__(self):
        return ''.join(str(cmd) for cmd in self)

    @functools.cached_property
    def payload_map(self):
        res = {cls.__name__.upper(): cls for cls in self.__commands__}
        res.update(LINK=Link, TITLE=Title, ID=Id)
        return res

    @property
    def id(self):
        if self.ID:
            return self.ID.id

    @property
    def title(self):
        if self.TITLE:
            return self.TITLE.title

    @property
    def links(self):
        return {link.block: link.title for link in self.commands['LINK']}

    @property
    def linked_blocks(self):
        res = {}
        for name, title in self.links.items():
            for block in self.nexus.blocks.get(name, []):
                if block.title == title:
                    res[name] = block
        return res

    def __getattribute__(self, name):
        if name.isupper():
            try:
                return self.commands[name][0]
            except IndexError:
                return None
        return super().__getattribute__(name)

    @functools.cached_property
    def name(self):
        return get_name(self[0].iter_payload_tokens())

    @functools.cached_property
    def commands(self):
        res = collections.defaultdict(list)
        for cmd in self:
            if not (cmd.is_beginblock or cmd.is_endblock):
                cls = self.payload_map.get(cmd.name, Payload)
                res[cmd.name].append(cls(tuple(cmd.iter_payload_tokens()), nexus=self.nexus))
        return res

    def validate(self, log=None):
        ncmds = sum(len(cmds) for cmds in self.commands.values())
        if log:
            log.debug('{} block with {} commands'.format(self.name, ncmds))
        return True

    @classmethod
    def from_commands(cls,
                      commands: typing.Iterable[
                          typing.Union[str, typing.Tuple[str, str], typing.Tuple[str, str, str]]],
                      nexus: typing.Optional["Nexus"] = None,
                      name: typing.Optional[str] = None,
                      comment: typing.Optional[str] = None,
                      TITLE: typing.Optional[str] = None,
                      LINK: typing.Optional[str] = None,
                      ID: typing.Optional[str] = None) -> 'Block':
        """
        Generic factory method for blocks.

        This method will create a block with the uppercase name of the ``cls`` as name (or the
        explicitly passed block ``name``). The (name str, payload str) tuples from ``commands``
        are simply passed to :meth:`commonnexus.command.Command.from_name_and_payload` to assemble
        the commands in the block.

        This method should be used to create custom, non-public NEXUS blocks, while for public
        blocks the ``from_data`` method of the class implementing the block should be preferred,
        because the latter will make sure that consistent, valid block data is written.

        :param commands: The commands to be inserted in the body of the block. A command can be \
        specified as single string, which is taken as the name of the command, a pair \
        (name, payload) or a triple (name, payload, comment).
        :param nexus: A Nexus instance to lookup global config options.
        :param name: Explicit name of the block to be created.
        :return: The instantiated Block object.

        .. code-block:: python

            >>> from commonnexus import Nexus, Block
            >>> nex = Nexus()
            >>> nex.append_block(Block.from_commands([('mycommand', 'with data')], name='myblock'))
            >>> print(nex)
            #NEXUS
            BEGIN myblock;
                mycommand with data;
            END;
            >>> str(nex.MYBLOCK.MYCOMMAND)
            'with data'
        """
        cmds = [
            Command.from_name_and_payload('BEGIN', name or cls.__name__.upper(), comment=comment)]
        if TITLE:
            cmds.append(
                Command.from_name_and_payload(
                    'TITLE', Word(TITLE).as_nexus_string(), in_block=True))
        if ID:
            cmds.append(
                Command.from_name_and_payload('ID', Word(ID).as_nexus_string(), in_block=True))
        if LINK:
            if isinstance(LINK, str):
                block, _, title = LINK.partition('=')
                LINK = (block.strip(), title.strip())
            else:
                assert isinstance(LINK, tuple) and len(LINK) == 2
            cmds.append(Command.from_name_and_payload('LINK', '{} = {}'.format(
                Word(LINK[0]).as_nexus_string(), Word(LINK[1]).as_nexus_string()), in_block=True))
        for cmdspec in commands:
            payload, comment = None, None
            if isinstance(cmdspec, str):
                cname = cmdspec
            elif len(cmdspec) == 2:
                cname, payload = cmdspec
            elif len(cmdspec) == 3:
                cname, payload, comment = cmdspec
            else:
                raise ValueError(cmdspec)  # pragma: no cover
            cmds.append(
                Command.from_name_and_payload(cname, payload, comment=comment, in_block=True))
        cmds.append(Command.from_name_and_payload('END'))
        return cls(nexus, tuple(cmds))

    @classmethod
    def from_data(cls, *args, **kw) -> 'Block':
        """
        Block implementations must overwrite this method to implement "meaningful" NEXUS writing
        functionality.
        """
        raise NotImplementedError()  # pragma: no cover
