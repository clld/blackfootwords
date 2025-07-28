<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! active_menu_item = "values" %>
<%!
from blackfootwords import models
%>
<%block name="title">Lemmas</%block>
<h1>Lemmas</h1>
${request.get_datatable('values', models.Lemma).render()}