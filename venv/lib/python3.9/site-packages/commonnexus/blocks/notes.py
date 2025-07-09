import typing

from .base import Block, Payload
from commonnexus.tokenizer import iter_key_value_pairs, Word

if typing.TYPE_CHECKING:  # pragma: no cover
    from commonnexus.nexus import Nexus


class Text(Payload):
    """
    This command allows text to be attached to various objects.

    The SOURCE subcommand indicates the location of the text. The INLINE option indicates that the
    text is present at the end of the TEXT command; the FILE option indicates that it is in a
    separate file (the name of which is then specified in the TEXT subcommand); the RESOURCE option
    indicates that it is in the resource fork of the current file, in a resource of type TEXT (the
    numerical ID of which is then specified in the TEXT subcommand).

    For example, in the following

    .. code-block::

        TEXT TAXON=5 CHARACTER=2 TEXT='4 specimens observed';
        TEXT TAXON=Pan TEXT='This genus lives in Africa';
        TEXT CHARACTER=2 TEXT='Perhaps this character should be deleted';
        TEXT CHARACTER=1 STATE=0 TEXT='This state is hard to detect';

    the first command assigns the note "4 specimens observed" to the data entry for taxon 5,
    character 2; the second command assigns the note "Perhaps this character should be deleted" to
    character 2; the third command assigns the note "This genus lives in Africa" to the taxon Pan,
    and the last command assigns the note "This state is hard to detect" to state 0 of character 1.

    The text or source descriptor must be a single NEXUS word. If the text contains NEXUS
    whitespace or punctuation, it needs to be surrounded by single quotes, with any contained
    single quotes converted to a pair of single quotes.

    :ivar typing.List[str] taxons: list of taxon labels or numbers the text relates to.
    """
    def __init__(self, tokens=None, nexus=None, **kw):
        super().__init__(tokens, nexus=nexus)
        self.taxons = None
        self.characters = None
        self.states = None
        self.trees = None
        self.source = None
        self.text = None

        if self._tokens is None:
            for k, v in kw.items():
                setattr(self, k, v)
        else:
            for key, values in iter_key_value_pairs(self._tokens):
                key = key.lower()
                if key in ['taxon', 'character', 'state', 'tree']:
                    key = key + 's'
                else:
                    assert len(values) == 1
                    values = values[0]
                setattr(self, key.lower(), values)
            if self.nexus:
                for key in ['taxon', 'character', 'state', 'tree']:
                    key = key + 's'
                    if getattr(self, key):
                        kw = {}
                        if key == 'states':
                            kw['chars'] = self.characters
                        setattr(self, key, self.nexus.resolve_set_spec(
                            key[:-1].upper(), getattr(self, key), **kw))
            assert self.source in [None, 'FILE', 'INLINE'], self.source

    def as_payload(self):
        res = []
        if self.taxons:
            numbers = ' '.join(
                self.nexus.get_numbers('TAXON', self.taxons) if self.nexus else self.taxons)
            res.append("TAXON={}".format('({})'.format(numbers) if ' ' in numbers else numbers))

        if self.characters:
            numbers = ' '.join(self.nexus.get_numbers('CHARACTER', self.characters)
                               if self.nexus else self.characters)
            res.append("CHARACTER={}".format('({})'.format(numbers) if ' ' in numbers else numbers))

        #
        # FIXME: support STATE!
        #

        if self.trees:
            numbers = ' '.join(
                self.nexus.get_numbers('TREE', self.trees) if self.nexus else self.trees)
            res.append("TREE={}".format('({})'.format(numbers) if ' ' in numbers else numbers))

        res.append('SOURCE=INLINE')
        res.append('TEXT={}'.format(Word(self.text).as_nexus_string()))
        return ' '.join(res)


class Picture(Payload):
    """
    This command allows a picture to be attached to an object.

    The FORMAT subcommand allows specification of the graphics format of the image.
    The SOURCE subcommand indicates the location of the picture. The INLINE option indicates that
    the picture is present at the end of the PICTURE command; the FILE option indicates that it is
    in a separate file (the name of which is then specified in the PICTURE subcommand); the
    RESOURCE option indicates that it is in the resource fork of the current file, in a resource of
    type PICT (the numerical ID of which is then specified in the PICTURE command). The RESOURCE
    option is designed for AppleMacintosh® text files.

    For example, the following command

    .. code-block::

        PICTURE TAXON=5 CHARACTER=2 FORMAT=GIF SouRCE=file PiCTURE=wide.thorax.gif;

    assigns the image in the GIF-formatted file wide.thorax.gif to the data entry for taxon 5,
    character 2.

    The picture or source descriptor must be a single NEXUS word. If the picture contains NEXUS
    whitespace or punctuation, it needs to be surrounded by single quotes, with any contained
    single quotes converted to a pair of single quotes.

    Most graphics formats do not describe pictures using standard text characters. For this reason
    many images cannot be included INLINE in a NEXUS command unless they are converted into text
    characters. The ENCODE subcommand specifies the conversion mechanism used for inline images.

    .. warning::

        Support for encoding of type ``UUENCODE`` will be removed in Python 3.13, because

            `base64 is a modern alternative <https://docs.python.org/3/library/uu.html>`_
    """


class Notes(Block):
    """
    The NOTES block stores notes about various objects in a NEXUS file, including taxa, characters,
    states, and trees:

    .. rst-class:: nexus

        | BEGIN NOTES;
        |   [TEXT
        |     [TAXON=taxon-set]
        |     [CHARACTER=character-set]
        |     [STATE=state-set]
        |     [TREE=tree-set]
        |     SOURCE={INLINE | FILE | RESOURCE} TEXT=text-or-source-descriptor;]
        |   [PICTURE
        |     [TAX0N=taxon-set]
        |     [CHARACTER=character-set]
        |     [STATE= state-set]
        |     [TREE=tree-set]
        |     [FORMAT={PICT | TIFF | EPS | JPEG | GIF}]
        |     [ENCODE={NONE | UUENCODE | BINHEX}]
        |     SOURCE={INLINE | FILE | RESOURCE}
        |     PICTURE=picture-or-source-descriptor; ]
        | END;

    There are no restrictions on the order of commands.

    If the written description of the taxon-set, character-set, state-set, or tree-set contains
    more than one token, it must be enclosed in parentheses, as in the following example:

    .. code-block::

        TEXT TAXON=(1-3) TEXT= 'these taxa from the far north';

    If both a taxon-set and a character-set are specified, then the text or picture applies to
    those characters for those particular taxa. If both a character-set and a state-set are
    specified, then the text or picture applies to those states for those particular characters.

    .. warning::

        PICTURE and ``SOURCE=RESOURCE`` for TEXT is not supported by `commonnexus`.
    """
    __commands__ = {Text, Picture}

    @classmethod
    def from_data(cls,
                  texts: typing.List[typing.Dict[str, typing.Union[typing.List[str], str]]],
                  comment: typing.Optional[str] = None,
                  nexus: typing.Optional["Nexus"] = None,
                  TITLE: typing.Optional[str] = None,
                  ID: typing.Optional[str] = None,
                  LINK: typing.Optional[typing.Union[str, typing.Tuple[str, str]]] = None) \
            -> 'Block':
        cmds = [('TEXT', Text(nexus=nexus, **text).as_payload()) for text in texts]
        return cls.from_commands(cmds, nexus=nexus, TITLE=TITLE, ID=ID, LINK=LINK, comment=comment)

    @property
    def texts(self):
        return self.commands['TEXT']

    def get_texts(self, taxon=None, character=None, tree=None):
        res = []
        for text in self.texts:
            if (taxon and text.taxons and taxon in text.taxons) or \
                    (character and text.characters and character in text.characters) or \
                    (tree and text.trees and tree in text.trees):
                res.append(text)
        return res
