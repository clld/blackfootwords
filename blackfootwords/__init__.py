import collections
import functools

from clld import interfaces
from clld.db.models import common
from pyramid.config import Configurator
from clld.interfaces import IMapMarker, IValueSet, IValue, IDomainElement, IUnit, ISource
from clld.web.icon import MapMarker
from clldutils.svg import pie, icon, data_url
from clld.web.app import CtxFactoryQuery, menu_item
from clld.web.adapters.base import adapter_factory

# we must make sure custom models are known at database initialization!
from blackfootwords import models
from .models import Stem, Word, Morpheme
from .interfaces import IStem, IMorpheme


# _ is a recognized name for a function to mark translatable strings
_ = lambda s: s
_('Languages')
_('Parameters')
_('Values')
# _('Stems')

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.register_resource('stem', Stem, IStem, with_index=True)
    config.register_resource('morpheme', Morpheme, IMorpheme, with_index=True)
    config.register_resource('word', Word, IUnit, with_index=True)
    # config.register_resource('stem', Stem, IValue)
    # config.add_route('stems', '/stems')
    config.register_menu(
        ('dataset', functools.partial(menu_item, 'dataset', label='Home')),
        ('parameters', functools.partial(menu_item, 'parameters')),
        ('values', functools.partial(menu_item, 'values')),
        ('stems', lambda ctx, req: (req.route_url('stems'), 'Stems')),
        ('morphemes', lambda ctx, req: (req.route_url('morphemes'), 'Morphemes')),
        ('words', lambda ctx, req: (req.route_url('words'), 'Words')),
        ('languages', functools.partial(menu_item, 'languages')),
        ('sources', functools.partial(menu_item, 'sources')),
    ) 
    config.scan()

    return config.make_wsgi_app()
