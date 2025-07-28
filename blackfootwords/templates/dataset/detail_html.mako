<%inherit file="../home_comp.mako"/>

<%def name="sidebar()">
    <div class="well">
        <h3>Cite</h3>
        ${h.newline2br(h.text_citation(request, ctx))|n}
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
    Version 1.1 of the database includes words from nine different sources. The earliest source is from 1743 and the most recent source is from 1969, which means that all of the words are Old Blackfoot. PDFs of the sources can be downloaded from the Sources page.
    <br><br>
    In Version 1.1 many (but not all) of the words are analyzed into stems and even morphemes. The full analysis will be published soon as Version 1.2.
</p>
<br>
<p class="lead">
    Language acknowledgement
</p>

<p>
The Blackfoot language belongs to the people of the four Blackfoot Nations: the Siksikaiitsitapi, Kainaiitsitapi, Aapatohsipikani, and Aamsskaapipikani. I do not own the words or data in this database and I do not make any money from this project.
</p>