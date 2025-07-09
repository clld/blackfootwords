import functools
import itertools

from .tokenizer import TokenType, iter_tokens, Token, get_name


class Command(tuple):
    """
    From the specification:

        A command is a collection of tokens terminated by a semicolon. Commands cannot contain
        semicolons, except as terminators, unless the semicolons are contained within a comment
        or within a quoted token consisting of more than one text character.
    """
    @functools.cached_property
    def name(self):
        return get_name(self)

    def __str__(self):
        return ''.join(str(t) for t in self)

    def __eq__(self, other):  # To make command removal in Nexus.replace_block work.
        return id(self) == id(other)

    @classmethod
    def from_name_and_payload(cls, name, payload='', comment=None, in_block=False):
        tokens = []
        if comment:
            tokens.extend([Token('\n', TokenType.WHITESPACE), Token(comment, TokenType.COMMENT)])
        tokens.append(Token('\n', TokenType.WHITESPACE))
        name = list(iter_tokens(iter(name)))
        assert len(name) == 1 and name[0].type == TokenType.WORD
        tokens.extend(name)
        semicolons = 0
        if payload:
            tokens.append(Token(' ', TokenType.WHITESPACE))
            payload = list(iter_tokens(iter(payload)))
            semicolons = len([t for t in payload if t.is_semicolon])
            assert semicolons == 0 or (semicolons == 1 and payload[-1].is_semicolon)
            tokens.extend(payload)
        if semicolons == 0:
            tokens.append(Token(';', TokenType.PUNCTUATION))
        return cls(tokens)

    def without_comments(self) -> 'Command':
        """
        Returns a `Command` instance based on the tokens of `self`, but with all non-command
        comments removed.

        .. note::

            Command comment.—A comment containing a command is a command comment. Comments
            containing commands are indicated by a special symbol (\\ or &) as the first text
            character within the comment.

        .. warning::

            This will also remove comments in Newick representations of trees if these do not
            follow the NEXUS "command comment" conventions.
        """
        return Command(t for t in self if t.type != TokenType.COMMENT or t.text[0] in '&\\')

    def with_normalised_whitespace(self):
        comments, name, postcomments = [], [], []
        i, j = -1, -1
        for i, token in enumerate(self):
            if token.type == TokenType.WORD:
                name.append(token)
                break
            if token.type == TokenType.COMMENT:
                comments.append(token)
        for j, token in enumerate(self):
            if j <= i:
                continue
            if token.type == TokenType.WORD:
                name.append(token)
            elif token.type == TokenType.COMMENT:
                postcomments.append(token)
            else:
                break

        tokens = []
        if comments:
            tokens.append(Token('\n', TokenType.WHITESPACE))
            tokens.extend(comments)
        tokens.append(Token(
            '\n' if self.is_beginblock or self.is_endblock else '\n\t', TokenType.WHITESPACE))
        tokens.append((Token(''.join(t.text.upper() for t in name), TokenType.WORD)))
        if postcomments:
            tokens.extend(postcomments)
        tokens.extend(self[j:])
        return Command(tokens)

    @property
    def is_beginblock(self) -> bool:
        return self.name == 'BEGIN'

    @property
    def is_endblock(self) -> bool:
        # In MacClade, PAUP, and COMPONENT, the ENDBLOCK command has been used as
        # a synonym of the END command.
        return self.name in ['END', 'ENDBLOCK']

    def iter_payload_tokens(self, type=None):
        found = False
        for t in itertools.dropwhile(
                lambda t: t.type != TokenType.WHITESPACE,
                itertools.dropwhile(
                    lambda t: t.type in {TokenType.WHITESPACE, TokenType.COMMENT}, self[:-1])):
            if not found and t.type == TokenType.WHITESPACE:
                # Drop the first whitespace token, too.
                continue
            found = True
            if type is None or (type == t.type):
                yield t
