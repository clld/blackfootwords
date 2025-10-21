# Copyright (c) 2006-2021  Andrey Golovizin
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re

terminators = '.', '?', '!'
delimiter_re = re.compile(r'([\s\-])')
whitespace_re = re.compile(r'\s+')


def is_terminated(text):
    """
    Return True if text ends with a terminating character.

    >>> is_terminated('')
    False
    >>> is_terminated('.')
    True
    >>> is_terminated('Done')
    False
    >>> is_terminated('Done. ')
    False
    >>> is_terminated('Done.')
    True
    >>> is_terminated('Done...')
    True
    >>> is_terminated('Done!')
    True
    >>> is_terminated('Done?')
    True
    >>> is_terminated('Done?!')
    True
    """

    return text.endswith(terminators)


def add_period(text):
    """Add a period to the end of text, if needed.

    >>> print(add_period(''))
    <BLANKLINE>
    >>> print(add_period('.'))
    .
    >>> print(add_period('Done'))
    Done.
    >>> print(add_period('Done. '))
    Done. .
    >>> print(add_period('Done.'))
    Done.
    >>> print(add_period('Done...'))
    Done...
    >>> print(add_period('Done!'))
    Done!
    >>> print(add_period('Done?'))
    Done?
    >>> print(add_period('Done?!'))
    Done?!
    """

    if text and not is_terminated(text):
        return text + '.'
    return text


def abbreviate(text, split=delimiter_re.split):
    """Abbreviate the given text.

    >> abbreviate('Name')
    'N'
    >> abbreviate('Some words')
    'S. w.'
    >>> abbreviate('First-Second')
    'F.-S.'
    """

    def abbreviate(part):
        if part.isalpha():
            return part[0] + '.'
        else:
            return part

    return ''.join(abbreviate(part) for part in split(text))


def normalize_whitespace(string):
    r"""
    Replace every sequence of whitespace characters with a single space.

    >>> print(normalize_whitespace('abc'))
    abc
    >>> print(normalize_whitespace('Abc def.'))
    Abc def.
    >>> print(normalize_whitespace(' Abc def.'))
    Abc def.
    >>> print(normalize_whitespace('Abc\ndef.'))
    Abc def.
    >>> print(normalize_whitespace('Abc\r\ndef.'))
    Abc def.
    >>> print(normalize_whitespace('Abc    \r\n\tdef.'))
    Abc def.
    >>> print(normalize_whitespace('   \nAbc\r\ndef.'))
    Abc def.
    """

    return whitespace_re.sub(' ', string.strip())
