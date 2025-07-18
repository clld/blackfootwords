<%inherit file="app.mako"/>
<link href="${request.static_url('blackfootwords:static/css/introjs.min.css')}" rel="stylesheet">
<link href="${request.static_url('blackfootwords:static/project.css')}" rel="stylesheet">

##
## define app-level blocks:
##
<%block name="brand">
    <a class="brand" href="${request.route_url('dataset')}">Blackfoot Words</a>
    ##<a href="${request.route_url('dataset')}">
    ##    <img src="${request.static_url('blackfootwords:static/header.gif')}"/>
    ##</a>
</%block>

${next.body()}
