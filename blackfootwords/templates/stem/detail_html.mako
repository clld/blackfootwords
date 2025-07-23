<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "stems" %>
<%!
from blackfootwords import models
%>

<h2>${_('Stem ')}<span style="color: #014d4e">${ctx.domainelement.name if ctx.domainelement else ctx.name}</span></h2>
<dl>
    <dt>Lemma:</dt>
    <dd>${h.link(request, ctx.lemma)}</dd>
    <dt>Translation:</dt>
    <dd>${h.link(request, ctx.lemma.valueset.parameter)}</dd>
    % if ctx.word:
    <dt>Contained in word:</dt>
    <dd>${h.link(request, ctx.word)}</dd>
    % endif
    % for k, v in ctx.datadict().items():
    <dt>${k}</dt>
    <dd>${v}</dd>
    % endfor
</dl>