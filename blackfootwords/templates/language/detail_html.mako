<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%!
from blackfootwords import models
%>
<%! active_menu_item = "languages" %>
<%block name="title">${_('Language')} ${ctx.name}</%block>

<h2>${_('Dialect ')}<span style="color: #014d4e">${ctx.name}</span></h2>

${request.get_datatable('words', models.Word, language=ctx.name).render()}