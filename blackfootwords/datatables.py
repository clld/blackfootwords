from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.web.datatables.value import Values, ValueNameCol
from clld.db.util import get_distinct_values
from blackfootwords import models
from clld.web.datatables.base import DataTable

class ParameterCol(LinkCol):
    def get_obj(self, item):
        return item.valueset
    def get_attrs(self, item):
        return {'label': item.valueset.parameter.name}

class Lemmas(Values):
    def base_query(self, query):
        # Only include Lemmas, not Stems
        return query.filter(models.Lemma.polymorphic_type == 'lemma')
    def col_defs(self):
        res = [
            LinkCol(self, 'lemma'),
            ParameterCol(self, 'parameter', model_col=models.Concept.name, get_object=lambda i: i.valueset.parameter)
        ]
        res.append(Col(
            self,
            'categories',
            model_col=models.Lemma.categories,
            choices=get_distinct_values(models.Lemma.categories),
        ))
        return res


class StemFormCol(LinkCol):
    def get_obj(self, item):
        return item
    def get_attrs(self, item):
        return {'label': item.name}

class LemmaCol(LinkCol):
    def get_obj(self, item):
        return item.lemma
    def get_attrs(self, item):
        return {'label': item.lemma.name if item.lemma else 'N/A'}

class Stems(DataTable):
    def base_query(self, query):
        """Ensure the lemma relationship is loaded"""
        return query.options(joinedload(models.Stem.lemma))
    
    def col_defs(self):
        return [
            StemFormCol(self, 'form', model_col=models.Stem.name),
            LemmaCol(self, 'lemma', model_col=models.Lemma.name),
        ]


def includeme(config):
    """register custom datatables"""
    config.register_datatable('values', Lemmas)
    config.register_datatable('stems', Stems) 