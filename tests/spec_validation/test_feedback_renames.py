from spec_validation.feedback import DeclarationSelectorChange, LocatedResolvedReference, ReferenceRewrite, ReferenceUpdateIntent, verify_reference_updates
from spec_validation.models import DocumentSet, DocumentSnapshot, SnapshotIdentity, ValidationOptions
from spec_validation.parser import parse_document
from spec_validation.syntax import reference


def rename_case(tmp_path, updated_reference="UC8"):
    before_text = "## Use cases\n### 4. Original\nin --work--> out\n\n### Caller\nin --call--> out\n\nUses:\n- \"call\" -> UC4\n"
    after_text = before_text.replace("4. Original", "8. Renamed").replace('-> UC4', '-> ' + updated_reference) + "\n### 4. Replacement\nin --other--> out\n"
    before_doc = DocumentSnapshot.from_text("s.md", before_text)
    after_doc = DocumentSnapshot.from_text("s.md", after_text)
    options = ValidationOptions(workspace_root=tmp_path)
    before, after = (DocumentSet(documents=[doc], options=options) for doc in (before_doc, after_doc))
    old_owner, new_owner = (parse_document(doc, options).entities[0] for doc in (before_doc, after_doc))
    old_ref = reference("UC4", before_text.index("UC4"), before_doc)
    new_ref = reference(updated_reference, after_text.index(updated_reference), after_doc)
    intent = ReferenceUpdateIntent(
        before_snapshots=[SnapshotIdentity(document_id="s.md", content_sha256=before_doc.content_sha256, byte_count=before_doc.byte_count)],
        changes=[DeclarationSelectorChange(old_reference=old_ref, new_reference=reference("UC8", 0, after_doc), before_location=old_owner.source, after_location=new_owner.source)],
        incoming_references=[LocatedResolvedReference(reference=old_ref, target_location=old_owner.source)],
        reference_search_scope=["s.md"], discovery_complete=True,
    )
    rewrites = [ReferenceRewrite(before_source=old_ref.source, after_reference=new_ref)]
    return before, after, intent, rewrites


def test_explicit_rename_updates_reference(tmp_path):
    assert verify_reference_updates(*rename_case(tmp_path)).complete


def test_reused_number_is_wrong_target_even_when_it_exists(tmp_path):
    result = verify_reference_updates(*rename_case(tmp_path, "UC4"))
    assert not result.complete
    assert [d.code for d in result.diagnostics] == ["REFERENCE_TARGET_CHANGED"]


def test_incomplete_discovery_or_missing_rewrite_never_certifies(tmp_path):
    before, after, intent, rewrites = rename_case(tmp_path)
    intent.discovery_complete = False
    assert not verify_reference_updates(before, after, intent, rewrites).complete
    intent.discovery_complete = True
    assert not verify_reference_updates(before, after, intent, []).complete


def test_stale_reference_inventory(tmp_path):
    before, after, intent, rewrites = rename_case(tmp_path)
    intent.before_snapshots = []
    assert "STALE_REFERENCE_INTENT" in [d.code for d in verify_reference_updates(before, after, intent, rewrites).diagnostics]
