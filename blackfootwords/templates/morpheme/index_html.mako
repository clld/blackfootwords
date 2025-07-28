<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! active_menu_item = "morphemes" %>
<%!
from blackfootwords import models
%>
<%block name="title">Morphemes</%block>
<h1>Morphemes</h1>
${request.get_datatable('morphemes', models.Morpheme).render()}