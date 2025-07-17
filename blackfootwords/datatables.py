from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.web.datatables.value import Values
from blackfootwords import models

class FormCol(Col):
    def format(self, item):
        return item.name  # The form value

class ParameterCol(Col):
    def format(self, item):
        return item.valueset.parameter.name  # The parameter (translation)

class CommentCol(Col):
    def format(self, item):
        return item.description or ''

class CustomValues(Values):
    def col_defs(self):
        return [
            FormCol(self, 'Form'),
            ParameterCol(self, 'Parameter'),
            CommentCol(self, 'Comment'),
        ]

def includeme(config):
    """register custom datatables"""
    config.register_datatable('values', CustomValues)