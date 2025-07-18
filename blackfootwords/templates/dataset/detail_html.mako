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
    Abstract.
</p>
<p>
    More content.
</p>
