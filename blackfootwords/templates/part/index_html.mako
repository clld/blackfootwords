<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! active_menu_item = "parts" %>
<%!
from blackfootwords import models
%>
<%block name="title">Parts of Word</%block>
<h1>Parts of Word</h1>
${request.get_datatable('parts', models.Part).render()}