<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! active_menu_item = "stems" %>
<%!
from blackfootwords import models
%>
<%block name="title">Stems</%block>
<h1>Stems</h1>
${request.get_datatable('stems', models.Stem).render()}