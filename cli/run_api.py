"""FastAPI application runner."""

import argparse
import multiprocessing
import uvicorn


def main():
    """Run the FastAPI application with uvicorn."""
    parser = argparse.ArgumentParser(description="Run the OCR Facturas API server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development only)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: auto-detect CPU count, ignored with --reload)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Calculate workers if not specified and not in reload mode
    workers = 1 if args.reload else (args.workers or multiprocessing.cpu_count())

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=workers,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
