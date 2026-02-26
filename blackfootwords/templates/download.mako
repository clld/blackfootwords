<%inherit file="home_comp.mako"/>

<h3>Downloads</h3>

% if req.registry.settings.get('clld.zenodo_concept_doi'):
${util.dataset_download()}
% else:
<div class="span6">
    <p>
        Blackfoot Words is archived on 
        ${h.external_link("http://dx.doi.org/10.5281/zenodo.5774980", label="Zenodo")}.
    </p>
</div>
% endif
