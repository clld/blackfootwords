<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "values" %>
<%!
from blackfootwords import models
%>

<h2>${_('Lemma ')}<span style="color: #014d4e">${ctx.domainelement.name if ctx.domainelement else ctx.name}</span></h2>
<dl>
    <dt>Translation:</dt>
    <dd>${h.link(request, ctx.valueset.parameter)}</dd>
    % if ctx.valueset.references:
    <dt>References</dt>
    <dd>${h.linked_references(request, ctx.valueset)|n}</dd>
    % endif
    % for k, v in ctx.datadict().items():
    <dt>${k}</dt>
    <dd>${v}</dd>
    % endfor
    
    <dt>Stems:</dt>
    ${request.get_datatable('stems', models.Stem, lemma=ctx).render()}

    ##<dt>Morphemes:</dt>
    ##${request.get_datatable('morphemes', models.Morpheme, lemma=ctx).render()}
</dl>