# Layered planning Markdown validation

This isolated Pydantic library parses mixed story/spec Markdown, preserves source spans and invalid entries, and collects structural and reference errors. It checks both directions of realization mappings, exact number/title/requirement aliases, duplicates, cycles, anchors, and invariant references. It never edits input files, fetches references, starts the application, or imports database modules.

Version 0.2.3 matches the layered-spec version. Main workflows and embedded `Detailed Workflow` chains use the same `WorkflowChain`/`WorkflowExpression` models. Expressions retain states/types, named transitions, sequences, parallel branches, conditional branches, loops, and braced workflows. Parentheses produce `WorkflowParallel` with `kind="parallel"`; brackets produce `WorkflowConditional` with `kind="conditional"`. Original Markdown and source spans remain available in `chain.body` and `chain.source`.

Layers begin with a capitalized standalone label at column zero, such as `Requirements:` or `Detailed Workflow:`, preceded by a blank line. A first body label needs no leading blank. Unknown names, missing separators and obsolete `Layer:` prefixes produce diagnostics with recovery. Registered custom layers retain `Extension/<name>:` spelling.

Use `R4.1: definition` for an inline requirement. If the definition starts below, indent its marker by exactly two spaces (`  R4.1:`); ordinary continuation lines can be unindented. Indent standalone internal labels such as `  Input:` or `  Rules:` too. The general `Requirement: <exact identifier>` marker stays valid at column zero. Fenced/indented code, quotes, lists and HTML never declare outer layers.

The Pydantic classes are undeployed and require no migration. Report freshness still checks input snapshots and the current parser configuration.

`DetailedWorkflowLayer.content` preserves ordered `WorkflowProse`, `ValidWorkflowChain`, and `InvalidWorkflowChain` items; `.chains` selects the chain results. The layer may mix explanations and ordinary lists with named bullet workflows, two-space-indented standalone names, local headings, standalone arrow paragraphs/bullets, and text/workflow fences. Each fenced block holds one chain. Blank lines within groups do not truncate workflows. Inline examples inside prose, blockquotes, HTML, and other code languages remain Markdown. Quote or code-format prose that discusses arrow notation: a standalone unquoted arrow paragraph is interpreted as a workflow. Missing delimiters produce a retained invalid chain, and independently recognizable siblings remain available.

Python compatibility target: **3.10+**. The runtime passes Python 3.10 syntax checks, and the installed runtime dependencies permit Python 3.10. The regression suite has been executed on **Python 3.13**; execution on 3.10 remains unverified. Python 3.13 is the repository's development version, not a validator minimum.

Agent preparation follows the [shared validation procedure](../../skill/layered-spec-core/references/validation.md). Dependency installation requires user approval for the selected environment and manifest. After that approval, install and validate from the workspace root:

```powershell
python -m pip install -r skill/layered-spec-core/requirements.txt
python skill/layered-spec-core/scripts/validate_specs.py --workspace-root . --format json specs/validation-integration.md
```

Supply all participating Markdown files as positional arguments. Paths are relative to `--workspace-root`; cross-file locators are relative to their source document. There is one grammar and no `--dialect` flag. Numbered story aliases and uniquely resolvable local requirement shorthand remain supported; ambiguous references are errors.

Include related specifications needed to resolve references and check reciprocal mappings. Exclude lifecycle policy, ADRs and reference-only notes without structured regions. Missing reference context is not a pass; the validator does not fetch files automatically. From another directory, use absolute script and workspace-root paths. Report, log, env-file and rendered-output paths are relative to the current directory unless absolute.

Use `--format text` for human-readable output and `--report-json report.json` for an optional atomic report copy (its parent directory must exist). Defaults: 10 MiB/file, 100 MiB/set, depth 128, configurable through `--max-file-bytes`, `--max-total-bytes`, `--max-nesting-depth` (1–256). Input files cannot be report/log destinations. Logs default to `<workspace-root>/.agents/logs/spec_validation.log`; override with `--log-file`. Configuration does not depend on the backend: `--env-file` explicitly selects a dotenv file, and configured `LOGFIRE_TOKEN` enables Logfire when its optional dependency is installed. JSON stdout contains only the report.

Exit codes: **0** passed, **1** failed/incomplete, **2** invalid invocation/tool failure. A report includes snapshot hashes, option/input fingerprints, all located diagnostics, blocked checks and their causes, completeness, excluded semantic checks, and metrics. Timing fields vary; semantic diagnostics and ordering are deterministic.

No `.env` is loaded automatically. Select one with `--env-file <path>` when needed; a missing selected file is a tool error. Configuring `LOGFIRE_TOKEN` requires the optional `logfire` dependency in the same environment; its installation needs separate approval because it is outside the runtime manifest. File logging works without that optional dependency.

## Workflow configuration

The authoring agent owns this configuration independently of Python/Pydantic; direct CLI/library calls remain explicit validation operations and do not read it. Store `workflow.json` beside the active lifecycle `workflow.md`. Without an active lifecycle, including standalone skill use, use `<workspace-root>/specs/spec-lifecycle/workflow.json`. Do not create a second configuration merely because a task uses another spec directory. If an active lifecycle is subsequently moved or initialized elsewhere, move the existing configuration with it so a rejection is preserved.

The root is a JSON object with an optional `validation` section. Additional top-level sections are allowed for future workflow settings; preserve them when reading or updating validation. [default_workflow.json](../../skill/spec-first-planning-loop/assets/default_workflow.json) is the source of initial values. Copy it when workflow.json is missing, creating parent directories as needed; if only validation is absent, initialize just that section from the template. Existing settings survive skill updates and workflow restoration. Missing/invalid required templates and failed initialization are explicit setup errors. When present, `validation` is an object with exactly these three fields:

| Field | Values and meaning |
| --- | --- |
| `enabled` | Boolean; `false` prevents validation and setup prompts. |
| `python` | Executable path string or `null`. Resolve relative paths from the workspace root. Persist the selected executable, never a transient PATH alias. |
| `installation` | Object with `decision` (`ask`, `approved`, `rejected`) and `requirements_sha256` (64 hexadecimal characters for approval, otherwise `null`). |

An approved decision requires a nonempty interpreter path and the hash of the exact bytes of `skill/layered-spec-core/requirements.txt`. It authorizes only installation from that manifest into the agreed environment. Different targets, a recreated environment or changed requirements need new approval if setup is needed. Already satisfied dependencies require no installation or prompt. Never infer approval from generating this configuration, choosing a target alone or approving implementation of the validator. Use a platform-appropriate hash tool and quote the exact interpreter path in the proposed command.

Read the policy before probing interpreters. Malformed JSON, a non-object root, missing/unknown fields within a present validation section, invalid validation values or unreadable files are explicit setup errors. Other top-level sections are outside validation's scope. A disabled or rejected policy takes precedence over environment changes and persists across tasks/sessions. Within `validation`, rejection writes `enabled: false`, `decision: rejected`, and a null hash. Only an explicit user request re-enables validation; set `enabled: true` and reset installation to `ask` with a null hash. Do not automatically re-enable on discovery of new runtimes. Preserve the selected interpreter unless the user changes it; a missing selected interpreter is reported without silently switching installation targets.

Write decisions before acting and read back the saved JSON. If persistence fails, honor the current decision in memory, report that it was not saved, and do not claim future sessions will remember it. Installation failure retains the scoped approval but is a setup error; it does not become validation success or automatically disable validation. Availability is observed each run, never stored. Disabled validation and unavailable Python permit preparation with an explicit validation-not-run limitation; pending approval or unexpected setup failures are reported distinctly. Previously found document errors remain unresolved until corrected.

```python
from pathlib import Path
import sys

# Library callers add the bundled scripts directory to their import path.
sys.path.insert(0, str(Path("skill/layered-spec-core/scripts").resolve()))
from spec_validation.api import validate_documents
from spec_validation.loading import load_document_set
from spec_validation.models import ValidationOptions

options = ValidationOptions(workspace_root=Path.cwd())
documents = load_document_set(["specs/example.md", "specs/implementation.md"], options)
result = validate_documents(documents, include_documents=True)
print(result.report.model_dump_json(indent=2))
# result.documents contains partial assemblies, strict valid models, and raw blocks.
```

`feedback.py` supplies report freshness, bounded repair tracking, and explicit before/after rename verification. The shared [validation procedure](../../skill/layered-spec-core/references/validation.md) describes the agent handoff and reference discovery contract. A passing report covers structure (including main/detailed workflow syntax) and references only; execution/type semantics, natural-language recursive-call target resolution, termination, requirement satisfaction, proof checking, and incoming references outside the declared set remain separate.

`FeedbackState` and `record_repair_attempt` track correction batches, defaulting to three attempts and stopping when input and diagnostic fingerprints repeat on two successive attempts. `report_is_current` compares the current input set and configuration with the report; edits invalidate earlier passing evidence. The preparing agent owns corrections and receives the report, affected source and declared scope.

For programmatic rename verification, capture `ReferenceUpdateIntent` before changing a use-case title/number or requirement identifier. Record before snapshots, the old-to-new declaration mapping and discovered incoming references. Update reciprocal and cross-file references, supply `ReferenceRewrite` records to `verify_reference_updates`, and validate the full affected set. Target existence alone cannot prove that a reused name or number still selects the intended declaration; the helper checks only the declared mapping and discovery scope.

The core folder can be copied to another workspace without backend or database configuration. Use an absolute script path when running from an unrelated directory.

## Markdown rendering and consistency checks

Every recognized layer supports optional `- Name:` subsections at column zero, with contents indented beneath the header. `LayerBase.subsections` stores the ordered `LayerSubsection` union. Nested labels and protected literals do not create peer subsections. A direct column-zero requirement resumes layer ownership. Ordinary bullets without a standalone trailing colon remain ordinary content.

`TypedSubsection` owns entries processed by its parent layer: requirements, realization/Uses mappings, anchors and supported test/reference fields keep their existing validation. `WorkflowSubsection` owns ordered prose and chains extracted using the same workflow models as the main chain. `DetailedWorkflowLayer.chains` combines direct and subsection chains; `LayerBase.all_entries` combines direct and subsection entries. Both are source-ordered derived views, not duplicated JSON storage. Plain sections use `MarkdownSubsection`; Invariants keeps the standard typed variants below and treats its custom bodies as Markdown.

Existing declaration syntax takes priority over generic headers. `- step1:` in Workflow anchors remains an invalid empty anchor. In Detailed Workflow, `- Name:` immediately followed by a chain still names that chain, including a malformed one. To group mixed explanation and workflows, put explanatory prose after the subsection header, followed by indented chains or named workflows. Duplicate workflow labels are checked across the whole layer. This is one level of optional grouping, not recursive subsection interpretation.

Recognizable requirement/use-case selectors in realization layers and source selectors in Uses also keep their declaration grammar; for example, malformed `- R1:` in Realized by is not a custom subsection.

The renderer retains grouping indentation for typed entries and chains. All three checks cover grouped models, including order, names, typed fields and preserved prose. Undeployed schema classes are generalized directly (`StructuredSubsection`, `LayerSubsection`); no migration or compatibility alias is provided. Version remains 0.2.3.

`InvariantsLayer.subsections` stores subsections in source order. Every standalone `- Name:` at subsection level ends the previous subsection, including custom names. `MarkdownSubsection` holds `name`, exact `body: MarkdownBody`, and header `source` for `Outline`, `Definitions` and custom subsections. General bodies are Markdown: declaration-looking examples inside them do not enter the reference index. Repeated custom names are preserved; standard subsection names remain unique. Custom-only and rationale-only layers are valid.

`RationaleSubsection`, `StateInvariantsSubsection` and `DerivationsSubsection` own their typed/invalid `entries`, raw body, header source, completeness and diagnostics. Malformed known sections remain invalid rather than becoming general Markdown. `InvariantsLayer.entries` holds layer-level requirements/errors only; `all_entries` is a derived source-ordered traversal used by validation. JSON stores each entry under its owner rather than duplicating that traversal.

Rationale notes are `ValidEntry(value=RationaleNote(...))` in `RationaleSubsection.entries`, with optional `rationale_id`, required `note: MarkdownBody` and `assessment`, optional `qualification`, `reason`, `replacement` Markdown bodies, `used_by: list[EntityRef]`, and `source`.

Canonical rendering generates subsection headers and general bodies from those models, plus typed syntax for known entries. General names/body text and subsection order participate in structural comparison. Lossless reconstruction and the three consistency checks retain their existing contracts.

```md
Invariants:
- Rationale:
  - `N1`:
    - note: Normalization preserves meaning.
    - assessment: qualified
    - qualification: Only for accepted input.
    - used by: D1, other.md#UC2/D2
  - note: The proposed optimization is fast enough.
    - assessment: unsupported
    - reason: Measurements are unavailable.
```

Named notes use N followed by positive dotted numbers; anonymous notes start with `  - note:`. Fields use four-space list markers and text continuations use at least six spaces. Text fields preserve everything after the colon, including leading spaces and internal line endings; terminal CR/LF separators are syntax. Assessment and used by occupy one line. All four assessment values are typed: supported, qualified, unsupported and rejected. Qualification is required for qualified notes; reason is required for unsupported/rejected notes. Only supported/qualified named notes may declare used by. Each target must be a local or owner/file-qualified derivation in the declared set. Named notes are indexed for structured references such as `UC1/N1`; free-form mentions remain prose.

The validator accumulates duplicate, missing-field, disallowed-use and unresolved-reference errors. It does not establish whether an assessment or derivation is correct. Canonical rendering generates the note fields from typed values in a stable order, retaining each Markdown body; lossless mode retains all original formatting. All rationale fields participate in the existing structural comparison.

The source-backed renderer uses `ParsedDocument`, including the snapshot and source ownership. Canonical mode regenerates typed headers, entries, references and workflow ASTs, while preserving unparsed source intervals. Requirement/assertion/proof text remains exact. It is not a detached-model serializer or a general Markdown editor: verbatim gaps remain owned by the source snapshot. Canonical formatting applies to recognized syntax; it does not globally normalize spaces or indentation.

```python
# Development only; this directory is not distributed with the skills.
sys.path.insert(0, str(Path("tests/spec_validation").resolve()))
from spec_markdown.rendering import render_markdown, reconstruct_bytes
from spec_markdown.roundtrip import check_roundtrip

parsed = validate_documents(documents, include_documents=True).documents[0]
canonical = render_markdown(parsed)
original_bytes = reconstruct_bytes(parsed)
checks = check_roundtrip(documents)
print(checks.model_dump_json(indent=2))
```

`reconstruct_bytes` joins recovered source fragments and restores the original UTF-8 BOM. The preservation check additionally audits retained Markdown bodies against their source spans. The structural check regenerates syntax, reparses the complete set, and compares meaningful fields, resolved reference identities, order, duplicates and verbatim fragments. The stability check renders again and compares canonical Markdown exactly. Each readable document receives all three results; invalid structural content blocks canonical checks while exact reconstruction remains available. Failures include deterministic field paths and expected/actual values. Unexpected implementation failures propagate instead of becoming a pass.

Run the three checks as parser/renderer development tests, separately from spec validation:

```powershell
python -m pytest -c tests/spec_validation/pytest.ini tests/spec_validation/test_rendering.py -q
```

The validator has no Markdown consistency option and does not import or execute these checks. Development callers invoke `spec_markdown.roundtrip.check_roundtrip` directly. Passing round trips cannot rule out a mistake shared by parser and renderer, so tests also contain independently specified models and canonical Markdown.

Write a generated document to a separate file (the output parent must exist):

```powershell
python tests/spec_validation/render_specs.py --workspace-root . specs/validation-integration.md --output rendered-spec.md --mode canonical
```

Use `--mode lossless` for byte-exact reconstruction, including malformed source. Canonical mode rejects incomplete syntax explicitly. The renderer CLI accepts optional `--env-file`, configures file/optional Logfire logging, refuses input/output/log aliases, and writes output atomically. Exit codes: 0 rendered, 1 rejected input/rendering request, 2 tool/output failure. The default log is `<workspace-root>/.agents/logs/spec_rendering.log`; `--log-file` overrides it. Rendering never rewrites the input. Version remains 0.2.3; no class migrations are introduced.
