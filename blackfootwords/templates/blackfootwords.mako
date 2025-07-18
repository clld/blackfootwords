<%inherit file="app.mako"/>

##
## define app-level blocks:
##
<%block name="brand">
    <a class="brand" href="${request.route_url('dataset')}">Blackfoot Words</a>
</%block>

${next.body()}
