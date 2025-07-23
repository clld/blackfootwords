<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "words" %>
<%!
from blackfootwords import models
%>

<h2>${_('Word')} ${ctx.name}</h2>
<dl>
    <dt>Translation:</dt>
    <dd>${h.link(request, ctx.parameter)}</dd>
    <dt>Dialect:</dt>
    <dd>${h.link(request, ctx.language)}</dd>
    % for k, v in ctx.datadict().items():
    <dt>${k}</dt>
    <dd>${v}</dd>
    % endfor
</dl>
