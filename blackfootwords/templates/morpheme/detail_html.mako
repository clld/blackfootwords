<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "morphemes" %>
<%!
from blackfootwords import models
%>

<h2>${_('Morpheme')} ${ctx.domainelement.name if ctx.domainelement else ctx.name}</h2>
<dl>
    <dt>Contained in stem:</dt>
    <dd>${h.link(request, ctx.stem)}</dd>
    <dt>Lemmatized form of stem:</dt>
    <dd>${h.link(request, ctx.stem.lemma)}</dd>
</dl>