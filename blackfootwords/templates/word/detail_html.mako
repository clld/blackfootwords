<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "words" %>
<%!
from blackfootwords import models
%>

<h2>${_('Word ')}<span style="color: #014d4e">${ctx.name}</span></h2>
<dl>
    <dt>Translation:</dt>
    <dd>${h.link(request, ctx.parameter)}</dd>
    <dt>Dialect:</dt>
    <dd>${h.link(request, ctx.language)}</dd>

    <dt>Lab word Category:</dt>
    <dd>${ctx.category or 'N/A'}</dd>
    % if ctx.original_category:
        <dt>Original category:</dt>
        <dd>${ctx.original_category or 'N/A'}</dd>
    % endif
    % if ctx.original_ur:
        <dt>Original UR:</dt>
        <dd>${ctx.original_ur or 'N/A'}</dd>
    % endif
    
    % if ctx.original_phrase:
        <dt>Original phrase:</dt>
        <dd>${ctx.original_phrase or 'N/A'}</dd>
    % endif
    % if ctx.original_phrase_translation:
        <dt>Original phrase translation:</dt>
        <dd>${ctx.original_phrase_translation or 'N/A'}</dd>
    % endif
    % if ctx.original_phrase_ur:
        <dt>Original phrase UR:</dt>
        <dd>${ctx.original_phrase_ur or 'N/A'}</dd>
    % endif

    % if ctx.cited_from:
        <dt>Cited from:</dt>
        <dd>${ctx.cited_from or 'N/A'}</dd>
    % endif
    % if ctx.original_comments:
        <dt>Original comments:</dt>
        <dd>${ctx.original_comments or 'N/A'}</dd>
    % endif
    % if ctx.comments:
        <dt>Lab comments:</dt>
        <dd>${ctx.comments or 'N/A'}</dd>
    % endif

    <dt>Parts of word:</dt>
    ${request.get_datatable('parts', models.Part, word=ctx).render()}

    ##<pre>
    ##pk=${ctx.pk}
    ##len(ctx.data)=${len(list(ctx.data))}
    ##datadict=${getattr(ctx, 'datadict', lambda: {})()}
    ##</pre>



    <% extras = getattr(ctx, 'datadict', lambda: {})() %>
    % if extras:
        <h3>Additional information</h3>
        <table class="table table-condensed">
            % for k, v in sorted(extras.items()):
                % if v:
                    <tr><th>${k}</th><td>${v}</td></tr>
                % endif
            % endfor
        </table>
    % endif
</dl>
