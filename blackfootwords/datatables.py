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


def includeme(config):
    """register custom datatables"""
    config.register_datatable('values', Lemmas)
