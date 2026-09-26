"""Validate layered planning Markdown without starting the application backend."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from spec_validation.api import validate_documents
from spec_validation.diagnostics import diagnostic
from spec_validation.loading import load_document_set
from spec_validation.models import DocumentSet, InputLocation, ValidationOptions
from spec_validation.reporting import build_report, ordered_diagnostics, render_text, write_report
from spec_validation.validator import GraphResult

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--log-file", type=Path, help="Defaults to <workspace-root>/.agents/logs/spec_validation.log")
    parser.add_argument("--env-file", type=Path, help="Explicit optional dotenv file for telemetry configuration")
    parser.add_argument("--max-file-bytes", type=int, default=10_485_760)
    parser.add_argument("--max-total-bytes", type=int, default=104_857_600)
    parser.add_argument("--max-nesting-depth", type=int, default=128)
    return parser


def main(argv: list[str] | None = None) -> int:
    """UC5/UC6: bootstrap environment/logging, validate, then publish one report."""
    args = build_parser().parse_args(argv)
    logger = logging.getLogger("spec_validation")
    handlers: list[logging.Handler] = []
    report = None
    try:
        options = ValidationOptions(
            workspace_root=args.workspace_root.resolve(),
            max_file_bytes=args.max_file_bytes, max_total_bytes=args.max_total_bytes,
            max_nesting_depth=args.max_nesting_depth,
        )
        if not options.workspace_root.is_dir():
            raise ValueError("workspace_root must be an existing directory")
    except (ValueError, ValidationError) as error:
        sys.stderr.write(f"Invalid validation invocation: {error}\n")
        return 2
    try:
        if args.env_file is not None:
            if not args.env_file.is_file():
                raise ValueError(f"Environment file does not exist: {args.env_file}")
            load_dotenv(args.env_file)
        if args.log_file is None:
            args.log_file = options.workspace_root / ".agents" / "logs" / "spec_validation.log"
        inputs = [(options.workspace_root / path).resolve() for path in args.files]
        if args.log_file.resolve() in inputs:
            raise ValueError("Log destination must not modify an input document")
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(args.log_file, encoding="utf-8")
        handlers.append(handler)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if os.environ.get("LOGFIRE_TOKEN"):
            import logfire

            logfire.configure(console=False)
            telemetry_handler = logfire.LogfireLoggingHandler()
            handlers.append(telemetry_handler)
            logger.addHandler(telemetry_handler)
        document_set = load_document_set(args.files, options)
        report = validate_documents(document_set)
        logger.info("Planning validation: status=%s files=%s errors=%s", report.status, report.metrics.files, report.metrics.errors)
        if args.report_json:
            try:
                target = args.report_json.resolve()
                if target in inputs:
                    raise ValueError("Report destination must not overwrite an input document")
                write_report(target, report)
            except (OSError, ValueError) as error:
                item = diagnostic("REPORT_WRITE_FAILED", str(error), InputLocation(document_id=str(args.report_json)), phase="tool")
                report.diagnostics = ordered_diagnostics(report.diagnostics + [item])
                report.status, report.analysis_complete = "tool_error", False
                report.metrics.errors += 1
        output = report.model_dump_json(indent=2) + "\n" if args.format == "json" else render_text(report)
        sys.stdout.write(output)
        return 0 if report.status == "passed" else 2 if report.status == "tool_error" else 1
    except Exception as error:
        # State: unexpected tool failure -> logged traceback and never a successful validation result.
        logger.exception("Planning validator failed")
        item = diagnostic("TOOL_FAILURE", f"{type(error).__name__}: {error}", InputLocation(document_id="<tool>"), phase="tool")
        if report is None:
            failed = DocumentSet(documents=[], options=options, input_paths=list(args.files), failed_inputs=[item])
            report = build_report(failed, [], GraphResult(diagnostics=[], checks=[], edges=[], reference_count=0, duration_ms=0), 0)
        else:
            report.diagnostics = ordered_diagnostics(report.diagnostics + [item])
            report.status, report.analysis_complete = "tool_error", False
            report.metrics.errors += 1
        try:
            sys.stdout.write(report.model_dump_json(indent=2) + "\n" if args.format == "json" else render_text(report))
        except OSError:
            logger.exception("Cannot write tool failure report to stdout")
        return 2
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
