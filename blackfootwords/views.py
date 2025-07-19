from pyramid.view import view_config
from pyramid.response import Response
from blackfootwords import models

@view_config(route_name='words', renderer='words/detail_html.mako')
def mypage_view(request):
    return {'title': 'Words'}