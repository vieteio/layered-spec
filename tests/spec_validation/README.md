# Validator development

Tests and fixtures live here; the single runtime remains in `skill/layered-spec-core/scripts/spec_validation/`. See the [runtime reference](runtime-reference.md) for models, grammar, APIs, configuration and rendering behavior. Test configuration adds the core's scripts directory to the import path without importing the backend or loading its environment.

From the repository root:

```text
python -m pip install -r tests/spec_validation/requirements.txt
python -m pytest -c tests/spec_validation/pytest.ini tests/spec_validation -q
```

The development requirements include the runtime manifest and add pytest. The compatibility target is Python 3.10+; runtime syntax and installed dependency constraints permit 3.10, but the suite has been executed on Python 3.13 only.

Keep fixtures next to the tests. Development-only Markdown generation and the three consistency checks live in `spec_markdown/`, with `render_specs.py` as the development renderer CLI. They import the shipped parser; no shipped runtime imports them. Run them only for parser/renderer development, never during spec preparation or validation. Include independently expected models and canonical Markdown because a parser and renderer can share the same mistake.

`test_portability.py` copies the ready skill core into a temporary directory and invokes validation from an unrelated directory with no backend or development modules. It checks feedback/correction and absence of Markdown tooling/check results. Renderer CLI checks run separately from its development location. Telemetry uses a local stub and does not contact external services.

`test_public_installation.py` additionally needs Node.js and executes both public installers across all supported hosts. It verifies installed runtime bytes, manifests, rewritten commands, preserved workflow configuration and actual reciprocal-error correction. It does not install dependencies or contact the package registry. Run the npm installer tests with `node --test scripts/npm/test/*.test.mjs`.
