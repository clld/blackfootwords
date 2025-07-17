<% bibrec = ctx.bibtex() %>
<%
from clld.lib.bibtex import Record

# Create a new Record with same ID and genre
clean_bibrec = Record(bibrec.genre, bibrec.id)
# Add all fields except 'note'
for k, v in bibrec.items():
    if k != 'note' and k != 'howpublished' and k != 'annote':
        clean_bibrec[k] = v
%>

<textarea class="input-block-level" id="md-${ctx.pk}">${clean_bibrec.text()}</textarea>
<script>
$(document).ready(function() {
    $("#md-${ctx.pk}").focus(function() {
        var $this = $(this);
        $this.select();

        // Work around Chrome's little problem
        $this.mouseup(function() {
            // Prevent further mouseup intervention
            $this.unbind("mouseup");
            return false;
        });
    });
    $("#md-${ctx.pk}").focus();
});
</script>
