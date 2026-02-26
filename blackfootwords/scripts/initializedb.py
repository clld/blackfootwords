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
        name="Blackfoot Words",
        publisher_name="Department of Linguistics, Yale University",
        publisher_place="New Haven",
        publisher_url="https://www.blackfootwords.com",
        license = "http://creativecommons.org/licenses/by/4.0/",
        jsondata = {
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},
    )
    DBSession.add(dataset)
    
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
        # ('Tyler Brown', True),
        # ('Joshua Celli', True),
        # ('McKenzie Denham', True),
        # ('Hailey Dykstra', True),
        # ('Nico Kidd', True),
        # ('Rodrigo Hernandez-Merlin', True),
        # ('Evan Hochstein', True),
        # ('Pinyu Hwang', True),
        # ('Diana Kulmizev', True),
        # ('Hannah Morrison', True),
        # ('Matty Norris', True),
        # ('Lena Venkatraman', True),
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
            comments=form['LabLemmaComments'],
            valueset=vs,
            polymorphic_type='lemma',
        )

    #words
    for word in args.cldf.iter_rows('words.csv', 'id', 'form', 'languageReference', 'parameterReference', 'LabWordCategory', 'OriginalPhrase', 'OriginalPhraseTranslation', 'LabComments'):
        # source_id = word['Source_ID'] 
        # source = data['Source'].get(source_id)
        language_id = word['languageReference']
        language = data['Variety'].get(language_id)
        parameter_id = word['parameterReference']
        parameter = data['Concept'].get(parameter_id)
        
        word_obj = data.add(
            models.Word,
            word['id'],
            id=word['id'],
            name=word['form'],
            # source=source,
            language=language,
            parameter=parameter,
            original_category = word['OriginalCategory'],
            original_ur = word['OriginalUR'],
            category = word['LabWordCategory'],
            original_partial_word = word['OriginalPartialWord'],
            original_partial_word_translation = word['OriginalPartialWordTranslation'],
            original_partial_word_category = word['OriginalPartialWordCategory'],
            original_partial_word_ur = word['OriginalPartialWordUR'],
            original_phrase = word['OriginalPhrase'],
            original_phrase_translation = word['OriginalPhraseTranslation'],
            original_phrase_ur = word['OriginalPhraseUR'],
            cited_from = word['CitedFrom'],
            original_comments = word['OriginalComments'],
            comments = word['LabComments'],
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

    # parts of words
    for part in args.cldf.iter_rows('partsofwords.csv', 'Part_ID', 'LabPart', 'Lemma_ID', 'Word_ID',
                                    'ContainedIn', 'Precedence', 'LabPartCategory', 'LabPartComments'):
        lemma_id = part['Lemma_ID']
        lemma = data['Lemma'].get(lemma_id)
        word_id = part['Word_ID']
        word = data['Word'].get(word_id)

        if not lemma:
            print(f"Warning: Lemma with id {lemma_id} not found for part {part['Part_ID']}")
            continue
        if not word:
            print(f"Warning: Word with id {word_id} not found for part {part['Part_ID']}")
            continue

        # prefix each part id to distinguish from stem and morpheme ids
        part_id = 'part-{}'.format(part['Part_ID'])
        # LabPartCategory is multivalued in CLDF (separator ' '); pycldf returns a list.
        lab_cat = part['LabPartCategory']
        lab_part_category = '/'.join(lab_cat) if isinstance(lab_cat, list) else (lab_cat or None)
        data.add(
            models.Part,
            part_id,
            id=part_id,
            name=part['LabPart'],
            valueset=lemma.valueset,
            lemma=lemma,
            word=word,
            # contained_in=part['ContainedIn'],
            # precedence=part['Precedence'],
            lab_part_category=lab_part_category,
            lab_part_comments=part['LabPartComments'],
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


    # w = DBSession.query(models.Word).first()
    # print("Word pk:", w.pk)
    # print("Unit_data for this word:", list(DBSession.query(common.Unit_data)
    #     .filter(common.Unit_data.object_pk == w.pk)))
    # print("datadict:", w.datadict())




def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
