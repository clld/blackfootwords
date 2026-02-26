<%inherit file="../home_comp.mako"/>

<%def name="sidebar()">
    <div class="well">
        <h3>Cite</h3>
        Natalie Weber (ed). (2026). Blackfoot Words. New Haven: Department of Linguistics, Yale University. (Available online at ${h.external_link("https://www.blackfootwords.com", label="https://www.blackfootwords.com")}, Accessed on YYYY-MM-DD.)
        ##${h.newline2br(h.text_citation(request, ctx))|n}
        ${h.cite_button(request, ctx)}
    </div>
</%def>

<h2>Welcome to Blackfoot Words: A Lexical Database</h2>

<p class="lead">
    About
</p>
<p>
    Blackfoot Words is a database of lexical forms in Blackfoot (Algonquian).
    <br><br>
    What does that mean? We have typed up the Blackfoot words and translations from older written sources, including wordlists, dictionaries, and grammars. We then add information to each word, like the stems and meaningful parts inside of them. We also provide links between words that are the same but spelled differently, and links between words that share similar parts and concepts.
    <br><br>
    The database and this website were created to provide access to a large amount of lexical data for the Blackfoot communities and for language researchers.
</p>
<br>
<p class="lead">
    What's inside?
</p>
<p>
    Version 1.2 of the database includes words from nine different sources. The earliest source is from 1743 and the most recent source is from 1969, which means that all of the words are Old Blackfoot. PDFs of the sources can be downloaded from the Sources page of the Blackfoot Words website.
    <br><br>
    Version 1.2 includes 4,557 inflected words, analyzed into 6,276 stems and 6,202 morphemes, representing 3,159 unique lemmas. All records are annotated with lexical category, hierarchical relationships, and other metadata.
</p>
<br>
<p class="lead">
    Language acknowledgement
</p>

<p>
The Blackfoot language belongs to the people of the four Blackfoot Nations: the Siksikaiitsitapi, Kainaiitsitapi, Aapatohsipikani, and Aamsskaapipikani. I do not own the words or data in this database and I do not make any money from this project.
</p>