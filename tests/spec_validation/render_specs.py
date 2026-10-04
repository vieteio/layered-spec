"""Development-only renderer for one parsed planning document."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

# Resolve the shipped runtime from this development entrypoint, independent of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill/layered-spec-core/scripts"))

from dotenv import load_dotenv

from spec_validation.loading import load_document_set
from spec_validation.models import ValidationOptions
from spec_validation.parser import parse_document
from spec_markdown.rendering import RenderingError, reconstruct_bytes, render_markdown

def main(argv: list[str] | None = None) -> int:
    """UC8: load one snapshot, render the selected mode and atomically publish output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("canonical", "lossless"), default="canonical")
    parser.add_argument("--log-file", type=Path, help="Defaults to <workspace-root>/.agents/logs/spec_rendering.log")
    parser.add_argument("--env-file", type=Path, help="Explicit optional dotenv file for telemetry configuration")
    args = parser.parse_args(argv)
    logger = logging.getLogger("spec_validation.rendering")
    handlers = []
    temporary = None
    try:
        if args.env_file is not None:
            if not args.env_file.is_file():
                raise FileNotFoundError(f"Environment file does not exist: {args.env_file}")
            load_dotenv(args.env_file)
        if args.log_file is None:
            args.log_file = args.workspace_root / ".agents" / "logs" / "spec_rendering.log"
        source_path = (args.workspace_root / args.file).resolve()
        target, log_path = args.output.resolve(), args.log_file.resolve()
        if source_path in (target, log_path) or target == log_path:
            raise ValueError("Input, output and log destinations must be distinct")
        if target.exists() and source_path.exists() and target.samefile(source_path):
            raise ValueError("Output aliases the input document")
        if log_path.exists() and source_path.exists() and log_path.samefile(source_path):
            raise ValueError("Log aliases the input document")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        handlers.append(handler)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if os.environ.get("LOGFIRE_TOKEN"):
            import logfire
            logfire.configure(console=False)
            handler = logfire.LogfireLoggingHandler()
            handlers.append(handler)
            logger.addHandler(handler)
        source = load_document_set([source_path], ValidationOptions(workspace_root=args.workspace_root.resolve()))
        if source.failed_inputs:
            raise RenderingError("; ".join(issue.message for issue in source.failed_inputs))
        document = parse_document(source.documents[0], source.options)
        if args.mode == "lossless":
            encoded = reconstruct_bytes(document)
        else:
            prefix = b"\xef\xbb\xbf" if document.snapshot.utf8_bom else b""
            encoded = prefix + render_markdown(document).encode("utf-8")
        # Valid complete output -> atomic replacement; an interrupted write never truncates output.
        with NamedTemporaryFile(dir=target.parent, prefix=".planning-render-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        os.replace(temporary, target)
        temporary = None
        logger.info("Rendered mode=%s bytes=%s output=%s", args.mode, len(encoded), target)
        sys.stdout.write(str(target) + "\n")
        return 0
    except (RenderingError, ValueError) as error:
        if handlers:
            logger.error("Rendering rejected: %s", error)
        sys.stderr.write(str(error) + "\n")
        return 1
    except Exception as error:
        if handlers:
            logger.exception("Rendering failed")
        sys.stderr.write(f"{type(error).__name__}: {error}\n")
        return 2
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
