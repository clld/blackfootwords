import itertools
import collections

from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clldutils.misc import slug

from pycldf import Sources

import blackfootwords
from blackfootwords import models


def main(args):
    data = Data()

    dataset = common.Dataset(
        id=blackfootwords.__name__,
        domain='www.blackfootwords.com',
        name="Blackfoot Words: A lexical database of Blackfoot legacy sources",
        publisher_name="Language Resources and Evaluation",
        publisher_place="",
        publisher_url="https://www.blackfootwords.com/",
        license = "http://creativecommons.org/licenses/by/4.0/",
        jsondata = {
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},
    )
    DBSession.add(dataset)
    # data.add(
    #     common.Dataset,
    #     blackfootwords.__name__,
    #     id=blackfootwords.__name__,
    #     domain='',

    #     publisher_name = "",
    #     publisher_place = "",
    #     publisher_url = "",
    #     license = "http://creativecommons.org/licenses/by/4.0/",
    #     jsondata = {
    #         'license_icon': 'cc-by.png',
    #         'license_name': 'Creative Commons Attribution 4.0 International License'},

    # )
    contrib = common.Contribution(
        id='cldf', name=dataset.name
    )
    # contrib = data.add(
    #     common.Contribution,
    #     None,
    #     id='cldf',
    #     name=args.cldf.properties.get('dc:title'),
    #     description=args.cldf.properties.get('dc:bibliographicCitation'),
    # )
    for i, spec in enumerate([
        ('Natalie Weber', True),
        ('Tyler Brown', True),
        ('Joshua Celli', True),
        ('McKenzie Denham', True),
        ('Hailey Dykstra', True),
        ('Nico Kidd', True),
        ('Rodrigo Hernandez-Merlin', True),
        ('Evan Hochstein', True),
        ('Pinyu Hwang', True),
        ('Diana Kulmizev', True),
        ('Hannah Morrison', True),
        ('Matty Norris', True),
        ('Lena Venkatraman', True),
    ]):
        name, primary = spec
        c = common.Contributor(id=slug(name), name=name)
        dataset.editors.append(common.Editor(contributor=c, ord=i, primary=primary))


    # dialects
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

    # sources
    for rec in bibtex.Database.from_file(args.cldf.bibpath, lowercase=True):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    refs = collections.defaultdict(list)

    # translations
    for param in args.cldf.iter_rows('ParameterTable', 'id', 'name'):
        data.add(
            models.Concept,
            param['id'],
            id=param['id'],
            name='{} [{}]'.format(param['name'], param['id']),
        )
    for form in args.cldf.iter_rows('FormTable', 'id', 'form', 'languageReference', 'parameterReference'):
    # for form in args.cldf.iter_rows('FormTable', 'id', 'form', 'parameterReference'):
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
            polymorphic_type='lemma',
        )

    #words
    for word in args.cldf.iter_rows('words.csv', 'id', 'form', 'languageReference', 'parameterReference'):
        # source_id = word['Source_ID']
        # source = data['Source'].get(source_id)
        language_id = word['languageReference']
        language = data['Variety'].get(language_id)
        parameter_id = word['parameterReference']
        parameter = data['Concept'].get(parameter_id)

        data.add(
            models.Word,
            word['id'],
            id=word['id'],
            name=word['form'],
            # source=source,
            language=language,
            parameter=parameter,
        )
    
    # stems
    for stem in args.cldf.iter_rows('stems.csv', 'id', 'form', 'formReference', 'Word_ID'):
        lemma_id = stem['formReference']
        lemma = data['Lemma'].get(lemma_id)
        word_id = stem['Word_ID']
        word = data['Word'].get(word_id)
        if not lemma:
            print(f"Warning: Lemma with id {lemma_id} not found for stem {stem['id']}")
            continue
        if not hasattr(lemma, 'valueset'):
            print(f"Warning: Lemma {lemma_id} has no valueset for stem {stem['id']}")
            continue
        if not word:
            print(f"Warning: Word with id {word_id} not found for stem {stem['id']}")
            continue
        data.add(
            models.Stem,
            stem['id'],
            id=stem['id'],
            name=stem['form'],
            lemma=lemma,
            word=word,
            valueset=lemma.valueset,
        )
    
    #morphemes
    for morpheme in args.cldf.iter_rows('morphemes.csv', 'id', 'form', 'Lemma_ID', 'Stem_ID'):
        lemma_id = morpheme['Lemma_ID']
        lemma = data['Lemma'].get(lemma_id)
        stem_id = morpheme['Stem_ID']
        stem = data['Stem'].get(stem_id)
        if not lemma:
            print(f"Warning: Lemma with id {lemma_id} not found for morpheme {morpheme['id']}")
            continue
        if not stem:
            print(f"Warning: Stem with id {stem_id} not found for morpheme {morpheme['id']}")
            continue
        data.add(
            models.Morpheme,
            morpheme['id'],
            id=morpheme['id'],
            name=morpheme['form'],
            valueset=lemma.valueset,
            lemma=lemma,
            stem=stem,
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
