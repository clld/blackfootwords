<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! active_menu_item = "words" %>
<%!
from blackfootwords import models
%>
<%block name="title">Words</%block>
<h1>Words</h1>
${request.get_datatable('words', models.Word).render()}