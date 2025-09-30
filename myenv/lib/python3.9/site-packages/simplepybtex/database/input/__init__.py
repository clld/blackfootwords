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

import io

import simplepybtex.io
from simplepybtex.database import BibliographyData
from simplepybtex.exceptions import PybtexError


class BaseParser:
    default_suffix = None
    filename = '<INPUT>'

    def __init__(self, encoding=None, wanted_entries=None, min_crossrefs=2, **kwargs):
        self.encoding = encoding or simplepybtex.io.get_default_encoding()
        self.data = BibliographyData(
            wanted_entries=wanted_entries,
            min_crossrefs=min_crossrefs,
        )

    def parse_file(self, filename):
        self.filename = filename
        open_file = simplepybtex.io.open_unicode
        with open_file(filename, encoding=self.encoding) as f:
            try:
                self.parse_stream(f)
            except UnicodeDecodeError as e:  # pragma: no cover
                raise PybtexError(str(e), filename=self.filename)
        return self.data

    def parse_string(self, value):  # pragma: no cover
        raise NotImplementedError

    def parse_bytes(self, value):
        assert not isinstance(value, str)
        return self.parse_string(value.decode(self.encoding))

    def parse_stream(self, stream):  # pragma: no cover
        raise NotImplementedError
