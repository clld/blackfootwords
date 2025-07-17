from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.web.datatables.value import Values
from clld.db.util import get_distinct_values
from blackfootwords import models

class Lemmas(Values):
    def col_defs(self):
        res = Values.col_defs(self)
        res.append(Col(
            self,
            'categories',
            model_col=models.Lemma.categories,
            choices=get_distinct_values(models.Lemma.categories),
        ))
        return res

# class FormCol(Col):
#     def format(self, item):
#         return item.name  # The form value

# class ParameterCol(Col):
#     def format(self, item):
#         return item.valueset.parameter.name  # The parameter (translation)

# class CommentCol(Col):
#     def format(self, item):
#         return item.labLemmaCategory or ''

# class CustomValues(Values):
#     def col_defs(self):
#         return [
#             FormCol(self, 'Form'),
#             ParameterCol(self, 'Parameter'),
#             CommentCol(self, 'Comment'),
#         ]

def includeme(config):
    """register custom datatables"""
    # config.register_datatable('values', CustomValues)
    config.register_datatable('values', Lemmas)