from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol, DetailsRowLinkCol
from clld.db.models.common import Language, LanguageSource, Source
from clld.web.datatables.value import Values, ValueNameCol
from clld.db.util import get_distinct_values
from blackfootwords import models
from clld.web.datatables.base import DataTable
from clld.lib.bibtex import EntryType
from clld.web.util.htmllib import HTML
from clld.web.util.helpers import (
    link, button, icon, JS_CLLD, external_link, linked_references, JSDataTable,
)


class LemmaCol(LinkCol):
    def get_obj(self, item):
        return item.lemma
    def get_attrs(self, item):
        return {'label': item.lemma.name if item.lemma else 'N/A'}
    
## lemmas table ##
class LemmaFormCol(LinkCol):
    def get_obj(self, item):
        return item
    def get_attrs(self,item):
        return {'label': item.name}
class ParameterCol(LinkCol):
    def get_obj(self, item):
        return item.valueset
    def get_attrs(self, item):
        return {'label': item.valueset.parameter.name}

class Lemmas(Values):
    # def base_query(self, query):
    #     # Only include Lemmas, not Stems
    #     return query.filter(models.Lemma.polymorphic_type == 'lemma')
    def col_defs(self):
        return [
            # LemmaFormCol(self, 'form', model_col=models.Lemma.name),
            LinkCol(self, 'lemma'),
            ParameterCol(self, 'parameter', model_col=models.Concept.name, get_object=lambda i: i.valueset.parameter),
            Col(self, 'categories', model_col=models.Lemma.categories, choices=get_distinct_values(models.Lemma.categories)),
        ]
    
## morphemes table ##
class MorphemeFormCol(LinkCol):
    def get_obj(self, item):
        return item
    def get_attrs(self, item):
        return {'label': item.name}
class MorphemeStemCol(LinkCol):
    def get_obj(self, item):
        return item.stem
    def get_attrs(self, item):
        return {'label': item.stem.name}
class Morphemes(DataTable):
    def __init__(self, req, model, **kw):
        super().__init__(req, model, **kw)
        self.lemma_filter = kw.get('lemma')
    def base_query(self, query):
        """Ensure the lemma relationship is loaded"""
        query = query.options(joinedload(models.Morpheme.lemma))
        if self.lemma_filter:
            query = query.filter(models.Morpheme.lemma == self.lemma_filter)
        return query
    def col_defs(self):
        return [
            MorphemeFormCol(self, 'form', model_col=models.Morpheme.name),
            LemmaCol(self, 'lemma', model_col=models.Lemma.name),
            MorphemeStemCol(self, 'stem', model_col=models.Stem.name),
        ]

## stems table ##
class StemFormCol(LinkCol):
    def get_obj(self, item):
        return item
    def get_attrs(self, item):
        return {'label': item.name}
class StemWordCol(LinkCol):
    def get_obj(self, item):
        return item.word
    def get_attrs(self, item):
        return {'label': item.word.name}
class Stems(DataTable):
    def __init__(self, req, model, **kw):
        super().__init__(req, model, **kw)
        self.lemma_filter = kw.get('lemma')
    
    def base_query(self, query):
        """Ensure the lemma relationship is loaded"""
        query = query.options(joinedload(models.Stem.lemma))
        
        # Handle lemma filtering if provided
        if self.lemma_filter:
            query = query.filter(models.Stem.lemma == self.lemma_filter)
        
        return query
    
    def col_defs(self):
        return [
            StemFormCol(self, 'form', model_col=models.Stem.name),
            LemmaCol(self, 'lemma', model_col=models.Lemma.name),
            StemWordCol(self, 'word', model_col=models.Word.name)
        ]


## words table ##
class WordFormCol(LinkCol):
    def get_obj(self, item):
        return item
    def get_attrs(self, item):
        return {'label': item.name}
    
class WordTranslationCol(LinkCol):
    def get_obj(self, item):
        return item.parameter
    def get_attrs(self, item):
        return {'label': item.parameter.name}
    
class WordLanguageCol(LinkCol):
    def get_obj(self, item):
        return item.language
    def get_attrs(self, item):
        return {'label': item.language.name}

class Words(DataTable):
    def col_defs(self):
        print("Words datatable is being used")
        return [
            WordFormCol(self, 'form', model_col=models.Word.name),
            WordTranslationCol(self, 'parameter', model_col=models.Concept.name, get_object=lambda i: i.parameter),
            WordLanguageCol(self, 'language', model_col=models.Variety.name)
        ]

## languages ##
class Languages(DataTable):
    def col_defs(self):
        return [
            LinkCol(self, 'name')
        ]

class CiteRowLinkCol(Col):

    __kw__ = {
        'bSearchable': False,
        'bSortable': False,
        'sClass': 'center',
        'sType': 'html',
        'sTitle': 'Cite',
        'button_text': 'Cite',
    }

    def format(self, item):
        return button(
            self.button_text,
            href=self.dt.req.resource_url(self.get_obj(item), ext='snippet.html'),
            title="show details",
            class_="btn-info details",
            tag=HTML.button)

class TypeCol(Col):

    """Render the BibTeX type of a Source item."""

    def __init__(self, dt, name, *args, **kw):
        kw['sTitle'] = 'BibTeX type'
        kw['choices'] = [(t.value, t.description) for t in EntryType]
        super(TypeCol, self).__init__(dt, name, *args, **kw)

    def format(self, item):
        return getattr(item.bibtex_type, 'description', '')

    def order(self):
        return Source.bibtex_type

    def search(self, qs):
        return Source.bibtex_type == getattr(EntryType, qs)


class Sources(DataTable):

    """Default DataTable for Source objects."""

    __constraints__ = [Language]
    __toolbar_kw__ = {'dl_formats': {'bib': 'BibTeX'}}

    def base_query(self, query):
        if self.language:
            query = query.join(LanguageSource)\
                .filter(LanguageSource.language_pk == self.language.pk)
        return query

    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            Col(self, 'description', sTitle='Title', format=lambda i: HTML.span(i.description)),
            Col(self, 'year'),
            Col(self, 'author'),
            TypeCol(self, 'bibtex_type'),
            CiteRowLinkCol(self, 'cite', sTitle="Citation"),
        ]


def includeme(config):
    """register custom datatables"""
    config.register_datatable('values', Lemmas)
    config.register_datatable('stems', Stems) 
    config.register_datatable('morphemes', Morphemes) 
    config.register_datatable('words', Words)
    config.register_datatable('languages', Languages)
    config.register_datatable('sources', Sources)