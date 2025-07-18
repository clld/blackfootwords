import itertools
import collections

from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex

from pycldf import Sources

import blackfootwords
from blackfootwords import models


def main(args):
    data = Data()
    data.add(
        common.Dataset,
        blackfootwords.__name__,
        id=blackfootwords.__name__,
        domain='',

        publisher_name = "",
        publisher_place = "",
        publisher_url = "",
        license = "http://creativecommons.org/licenses/by/4.0/",
        jsondata = {
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )


    contrib = data.add(
        common.Contribution,
        None,
        id='cldf',
        name=args.cldf.properties.get('dc:title'),
        description=args.cldf.properties.get('dc:bibliographicCitation'),
    )

    for lang in args.cldf.iter_rows('LanguageTable', 'id', 'glottocode', 'name', 'latitude', 'longitude'):
        data.add(
            models.Variety,
            lang['id'],
            id=lang['id'],
            name=lang['name'],
            latitude=lang['latitude'],
            longitude=lang['longitude'],
            glottocode=lang['glottocode'],
        )

    for rec in bibtex.Database.from_file(args.cldf.bibpath, lowercase=True):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    refs = collections.defaultdict(list)


    for param in args.cldf.iter_rows('ParameterTable', 'id', 'name'):
        data.add(
            models.Concept,
            param['id'],
            id=param['id'],
            name='{} [{}]'.format(param['name'], param['id']),
        )
    for form in args.cldf.iter_rows('FormTable', 'id', 'form', 'languageReference', 'parameterReference'):
    # for form in args.cldf.iter_rows('FormTable', 'id', 'form', 'parameterReference', 'comment'):
        vsid = (form['languageReference'], form['parameterReference'])
        # vsid = (form['parameterReference'])
        vs = data['ValueSet'].get(vsid)
        if not vs:
            vs = data.add(
                common.ValueSet,
                vsid,
                id='-'.join(vsid),
                language=data['Variety'][form['languageReference']],
                parameter=data['Concept'][form['parameterReference']],
            )

        data.add(
            models.Lemma,
            form['id'],
            id=form['id'],
            name=form['form'],
            categories='/'.join(form['LabLemmaCategory']),
            valueset=vs,
            # description=form['comment']
        )
    
    # for word in args.cldf.iter_rows('WordTable', 'id', 'form', 'source_id'):
    #     data.add(
    #         models.Words,
    #         word['id'],
    #         id=word['id'],
    #         form=word['form'],
    #         source_id=word['source_id'],
    #     )

    for (vsid, sid), pages in refs.items():
        DBSession.add(common.ValueSetReference(
            valueset=data['ValueSet'][vsid],
            source=data['Source'][sid],
            description='; '.join(nfilter(pages))
        ))



def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
