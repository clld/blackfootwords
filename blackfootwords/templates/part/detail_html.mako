<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parts" %>
<%!
from blackfootwords import models
%>

<h2>${_('Part of Word ')}<span style="color: #014d4e">${ctx.domainelement.name if ctx.domainelement else ctx.name}</span></h2>
<dl>
    <dt>Lemma:</dt>
    <dd>${h.link(request, ctx.lemma)}</dd>
    <dt>Translation:</dt>
    <dd>${h.link(request, ctx.lemma.valueset.parameter)}</dd>
    <dt>Contained in word:</dt>
    <dd>${h.link(request, ctx.word)}</dd> 
    % if ctx.lab_part_category:
        <dt>Category:</dt>
        <dd>${ctx.lab_part_category or 'N/A'}</dd>
    % endif
    % if ctx.lab_part_comments:
        <dt>Comments:</dt>
        <dd>${ctx.lab_part_comments or 'N/A'}</dd>
    % endif
</dl>