<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "morphemes" %>
<%!
from blackfootwords import models
%>

<h2>${_('Morpheme ')}<span style="color: #014d4e">${ctx.domainelement.name if ctx.domainelement else ctx.name}</span></h2>
<dl>
    <dt>Lemma:</dt>
    <dd>${h.link(request, ctx.lemma)}</dd>
    <dt>Contained in stem:</dt>
    <dd>${h.link(request, ctx.stem)}</dd>
    <dt>Contained in word:</dt>
    <dd>${h.link(request, ctx.stem.word)}</dd>
</dl>