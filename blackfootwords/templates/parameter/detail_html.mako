<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Translation')} ${ctx.name}</%block>
<%!
from blackfootwords import models
%>

<h2>${_('Translation ')}<span style="color: #014d4e">${ctx.name}</span></h2>

% if ctx.description:
<p>${ctx.description}</p>
% endif

<dt>Lemmas with this translation:</dt>
${request.get_datatable('values', models.Lemma, parameter=ctx).render()} 

<dt>Words with this translation:</dt>
${request.get_datatable('words', models.Word, parameter=ctx).render()} 