<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "sources" %>
<%block name="title">${_('Source')} ${ctx.id}</%block>

<% bibrec = ctx.bibtex() %>
<%
from clld.lib.bibtex import Record

# Create a new Record with same ID and genre
clean_bibrec = Record(bibrec.genre, bibrec.id)
# Add all fields except 'note'
for k, v in bibrec.items():
    if k != 'note' and k != 'howpublished':
        clean_bibrec[k] = v
%>

<div class="source-card" style="max-width: 600px; margin: 2em auto; padding: 2em; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); background: #fafbfc;">
    <h2 style="margin-top: 0;">${_('Source')} <span style="color: #555;">${ctx.name or ctx.id}</span></h2>

    <div class="tabbable">
        <ul class="nav nav-tabs">
            <li class="active"><a href="#tab1" data-toggle="tab">Text</a></li>
            <li><a href="#tab2" data-toggle="tab">BibTeX</a></li>
            <li><a href="#tab3" data-toggle="tab">RIS</a></li>
            <li><a href="#tab4" data-toggle="tab">MODS</a></li>
        </ul>

        <div class="tab-content" style="margin-top: 1em;">
            <div id="tab1" class="tab-pane active">
                <p>${clean_bibrec.text() | n}</p>
                % if ctx.datadict().get('Additional_information'):
                    <p>${ctx.datadict().get('Additional_information')}</p>
                % endif
                % if bibrec.get('url'):
                    <p>${h.external_link(bibrec['url'])}</p>
                % endif
                ${util.gbs_links(filter(None, [ctx.gbs_identifier]))}
                % if ctx.jsondata.get('internetarchive_id'):
                    <hr />
                    <iframe src='https://archive.org/stream/${ctx.jsondata.get('internetarchive_id')}?ui=embed#mode/1up' width='100%' height='500px' frameborder='1'></iframe>
                % endif
            </div>
            <div id="tab2" class="tab-pane"><pre>${bibrec}</pre></div>
            <div id="tab3" class="tab-pane"><pre>${bibrec.format('ris')}</pre></div>
            <div id="tab4" class="tab-pane"><pre>${bibrec.format('mods')}</pre></div>
        </div>
    </div>
    % if hasattr(ctx, 'note') and ctx.note:
        <div style="margin-bottom: 1.5em;">
            <h3 style="margin-bottom: 0.3em; color: #2a4d69; font-size: 1.1em;">Notes</h3>
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