"""

Punctuation
~~~~~~~~~~~

    Any of the following text characters are considered punctuation at some times:

    ..code-block::

        ( ) [ ] { } / \\ , ; : = * ' " " + - < >

    The following punctuation marks have special properties: [ ] do not break a
    word; + and - are allowed as state symbols, but none of the rest are allowed; - is
    considered punctuation except where it is the minus sign in a negative number.
"""
import enum
import itertools
import dataclasses

__all__ = [
    'TokenType', 'Token', 'iter_tokens', 'get_name', 'iter_words_and_punctuation', 'Word',
    'iter_delimited', 'iter_lines', 'word_after_equals', 'iter_key_value_pairs']

import typing

QUOTE = "'"
COMMENT = {'[': 1, ']': -1}
PUNCTUATION = r'(){}/\,;:=*"+-<>'
WHITESPACE = '\t\r\n '
BOOLEAN = {}
for s in 'yes 1 true'.split():
    BOOLEAN[s] = True
for s in 'no 0 false'.split():
    BOOLEAN[s] = False


class TokenType(enum.Enum):
    WORD = 1
    QWORD = 2
    COMMENT = 3
    PUNCTUATION = 4
    WHITESPACE = 5


@dataclasses.dataclass
class Token:
    """
    We parse Nexus in one pass, storing the data as list of tokens with enough
    information to extract relevant parts from this list later on.
    """
    __slots__ = ['text', 'type']
    text: str
    type: TokenType

    @classmethod
    def from_text(cls, tokens, type=None):
        return cls(
            text=''.join(tokens),
            type=type or (TokenType.WHITESPACE if tokens[-1] in WHITESPACE else TokenType.WORD))

    @property
    def is_semicolon(self):
        return self.type == TokenType.PUNCTUATION and self.text == ';'

    @property
    def is_whitespace(self):
        return self.type == TokenType.WHITESPACE

    @property
    def is_newline(self):
        return self.is_whitespace and any(c in self.text for c in '\r\n')

    @property
    def is_punctuation(self):
        return self.type == TokenType.PUNCTUATION

    def __str__(self):
        if self.type == TokenType.COMMENT:
            return '[{}]'.format(self.text)
        if self.type == TokenType.QWORD:
            return "{}{}{}".format(QUOTE, self.text.replace(QUOTE, QUOTE + QUOTE), QUOTE)
        return self.text


def iter_tokens(s):
    token, lookahead = [], None

    while True:
        try:
            c = lookahead or next(s)
            lookahead = None

            if c == QUOTE:  # A quoted string.
                doublequote = False
                if token:
                    if token[-1] in WHITESPACE:
                        yield Token.from_text(token, TokenType.WHITESPACE)
                    else:
                        raise ValueError()  # pragma: no cover
                    token = []

                while 1:
                    c = lookahead or next(s)
                    lookahead = None
                    while c != QUOTE:
                        token.append(c)
                        c = next(s)

                    if doublequote:
                        token.append(c)
                        doublequote = False
                    else:
                        try:
                            lookahead = next(s)
                        except StopIteration:
                            lookahead = None
                        if lookahead == QUOTE:
                            doublequote = True
                        else:  # End of quoted string
                            yield Token.from_text(token, type=TokenType.QWORD)
                            token = []
                            break
                continue

            if c == '[':  # A comment.
                if token:
                    yield Token.from_text(token)
                    token = []
                commentlevel = 1
                while 1:
                    c = next(s)
                    while c not in COMMENT:
                        token.append(c)
                        c = next(s)
                    commentlevel += COMMENT[c]
                    if commentlevel == 0:
                        yield Token.from_text(token, TokenType.COMMENT)
                        token = []
                        break
                    else:
                        token.append(c)
                continue

            if c in WHITESPACE:
                if token and (token[-1] not in WHITESPACE):
                    yield Token.from_text(token, TokenType.WORD)
                    token = []
                token.append(c)
                continue

            if c in PUNCTUATION:
                if token:
                    yield Token.from_text(token)
                    token = []
                yield Token.from_text(c, TokenType.PUNCTUATION)
                continue

            if token and (token[-1] in WHITESPACE):
                yield Token.from_text(token, TokenType.WHITESPACE)
                token = []
            token.append(c)

        except StopIteration:
            break

    if token:
        yield Token.from_text(token)


def get_name(tokens):
    """
    The Nexus spec allows comments **in** block or command names. This function takes this into
    account when assembling a name from an iterable of tokens.
    """
    res = ''
    for t in itertools.dropwhile(lambda t: t.type != TokenType.WORD, tokens):
        if res:
            # We already encountered one word.
            if t.type == TokenType.WORD:
                res += t.text
            elif t.type != TokenType.COMMENT:
                break
        else:
            res += t.text
    return res.upper()


class Word(str):
    def __eq__(self, other):
        return self.replace(' ', '_') == other.replace(' ', '_') \
            if isinstance(other, str) else False

    def as_nexus_string(self):
        must_quote = False
        for chars in [WHITESPACE, COMMENT, PUNCTUATION, QUOTE]:
            if any(c in self for c in chars):
                must_quote = True
                break
        if must_quote:
            return "{}{}{}".format(QUOTE, self.replace(QUOTE, QUOTE + QUOTE), QUOTE)
        return self

    def __hash__(self):
        return hash(str(self))


def iter_words_and_punctuation(tokens, allow_punctuation_in_word=None, nexus=None):
    """
    Word

    From the spec:

        Except for special cases involving quotes or comments, a NEXUS word is any string of text
        characters that is bounded by whitespace or punctuation and that does not contain
        whitespace or punctuation. If the first character of a word is a single quote, then
        the word ends with the next single quote (unless that single quote is in a pair of
        consecutive single quotes; if so, then the word ends at the first unpaired single quote).
        Any character, including punctuation and whitespace, may be contained within a quoted word.
        A word cannot consist of only whitespace and punctuation. On each of the following lines
        is a single legal word:

        .. code-block::

            Bembidion
            B._zephyrum
            'John''s sparrow (eastern) '

        Underscores are considered equivalent to blank spaces, except that underscores are dark
        characters and blank spaces are whitespace. Thus, a program encountering "B._zephyrum" and
        "'B. zephyrum'" should judge them to be identical.  Any doubled single quotes within a
        quoted word should be converted to single quotes within the program. Thus, 'John''s' would
        be treated internally within a program as John's. Of course, if the program writes out
        such a word to a NEXUS file, the quote should be redoubled, and quotes should be written
        around the word: 'John' 's.
        A string of dark characters is broken into several words by whitespace and any punctuation
        other than brackets, unless the string is surrounded by quotes.
        Thus, "[\\i]Bembidion_velox[\\p]_Linnaeus" consists of one word, as does
        '- - A single word', whereas "two()words" consists of four tokens: the word "two",
        two punctuation characters, and the word "words".
    """
    allow_punctuation_in_word = allow_punctuation_in_word or ''
    if nexus is not None:
        if nexus.cfg.hyphenminus_is_text:
            allow_punctuation_in_word += '-'
        if nexus.cfg.asterisk_is_text:
            allow_punctuation_in_word += "*"
    word = ''
    for i, token in enumerate(tokens):
        if token.type == TokenType.QWORD:
            assert not word
            yield token.text
        elif token.type == TokenType.WORD:
            word += token.text
        elif token.is_whitespace:
            if word:
                yield Word(word)
                word = ''
        elif token.is_punctuation:
            if token.text in allow_punctuation_in_word:
                word += token.text
            else:
                if word:
                    yield Word(word)
                    word = ''
                yield token
    if word:
        yield Word(word)


def iter_key_value_pairs(tokens, allow_punctuation_in_word=None):
    """
    :param tokens:
    :param allow_punctuation_in_word:
    :return:
    """
    key, e, value, b = None, False, [], False
    #
    # FIXME: need to pass nexus to iter_words_and_punctuation
    #
    for t in iter_words_and_punctuation(
            tokens, allow_punctuation_in_word=allow_punctuation_in_word):
        if key is None:
            assert isinstance(t, str)
            key = t
        elif not e:
            assert isinstance(t, Token) and t.text == '='
            e = True
        else:
            if isinstance(t, Token):
                if t.text == '(':
                    assert not value
                    b = True
                elif t.text == ')':
                    assert b
                    yield key, value
                    key, e, value, b = None, False, [], False
                else:
                    assert b
                    value.append(t.text)
            else:
                if b:
                    value.append(t)
                else:
                    assert not value
                    yield key, [t]
                    key, e, value, b = None, False, [], False


def word_after_equals(words_and_punctuation: typing.Generator) -> str:
    n = next(words_and_punctuation)
    assert n.text == '='
    res = next(words_and_punctuation)
    return res if isinstance(res, str) else res.text


def iter_lines(tokens):
    line = []
    for t in tokens:
        if t.is_newline:
            if not all(tt.type in (TokenType.WHITESPACE, TokenType.COMMENT) for tt in line):
                yield line
            line = []
        else:
            line.append(t)
    if line:
        if not all(tt.type in (TokenType.WHITESPACE, TokenType.COMMENT) for tt in line):
            yield line


def iter_delimited(start, words_and_punctuation, delimiter='"', allow_single_word=False):
    startchar = delimiter[0]
    endchar = startchar if len(delimiter) == 1 else delimiter[1]

    if isinstance(start, str) and start != startchar:
        if allow_single_word:
            yield start
            return
        raise ValueError("No delimiter found!")  # pragma: no cover
    else:
        start = start or next(words_and_punctuation)
        assert getattr(start, 'text', start) == startchar
        w = next(words_and_punctuation)
        while not (isinstance(w, Token) and w.text == endchar):
            yield w
            w = next(words_and_punctuation)
