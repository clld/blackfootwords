<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "sources" %>
<%block name="title">${_('Source')} ${ctx.id}</%block>

<div class="source-card" style="max-width: 600px; margin: 2em auto; padding: 2em; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); background: #fafbfc;">
    <h2 style="margin-top: 0;">${_('Source')} <span style="color: #555;">${ctx.name or ctx.id}</span></h2>

    % if hasattr(ctx, 'note') and ctx.note:
        <div style="margin-bottom: 1.5em;">
            <h3 style="margin-bottom: 0.3em; color: #2a4d69; font-size: 1.1em;">Orthography</h3>
            <div style="padding: 0.7em 1em; background: #f0f4f8; border-radius: 6px; color: #333;">${ctx.note | n}</div>
        </div>
    % endif
    % if hasattr(ctx, 'howpublished') and ctx.howpublished:
        <div style="margin-bottom: 1.5em;">
            <h3 style="margin-bottom: 0.3em; color: #2a4d69; font-size: 1.1em;">Provenance</h3>
            <div style="padding: 0.7em 1em; background: #f0f4f8; border-radius: 6px; color: #333;">${ctx.howpublished | n}</div>
        </div>
    % endif
    % if not (getattr(ctx, 'note', None) or getattr(ctx, 'howpublished', None)):
        <div style="color: #888; font-style: italic;">No additional notes for this source.</div>
    % endif
</div>