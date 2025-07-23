from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models import common
from clld.web.datatables.base import DataTable
from sqlalchemy import Column, Unicode, ForeignKey
from sqlalchemy.orm import relationship

from blackfootwords.interfaces import IStem, IWord

#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------

@implementer(interfaces.ILanguage)
class Variety(CustomModelMixin, common.Language):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    glottocode = Column(Unicode)

@implementer(interfaces.IValue)
class Lemma(CustomModelMixin, common.Value):
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)
    categories = Column(Unicode)
    __mapper_args__ = {'polymorphic_identity': 'lemma'}

@implementer(IStem)
class Stem(CustomModelMixin, common.Value):
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)
    lemma_pk = Column(Integer, ForeignKey('lemma.pk'))
    lemma = relationship('Lemma', backref='stems', foreign_keys=[lemma_pk])
    __mapper_args__ = {'polymorphic_identity': 'stem'}

@implementer(interfaces.IUnit)
class Word(CustomModelMixin, common.Unit):
    pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
    parameter_pk = Column(Integer, ForeignKey('parameter.pk'))
    parameter = relationship('Parameter', backref='words', foreign_keys=[parameter_pk])
    # source_pk = Column(Integer, ForeignKey('source.pk'))
    # source = relationship('Source', backref='sources', foreign_keys=[source_pk])

@implementer(interfaces.IParameter)
class Concept(CustomModelMixin, common.Parameter):
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
    concepticon_id = Column(Unicode)

