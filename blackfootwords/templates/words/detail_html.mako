<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "words" %>
<%block name="title">Words</%block>

<h1>Words</h1>
<p>This is a sample page for words.</p>

<div style="clear: both"/>
% if map_ or request.map:
${(map_ or request.map).render()}
% endif

${request.get_datatable('values', h.models.Contribution, parameter=ctx).render()}
