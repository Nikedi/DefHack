"""Compatibility shim for the legacy ``python -m DefHack`` entry point."""

from DefHack.sensors.images.ingest import (  # noqa: F401
    DEFAULT_API_KEY,
    DEFAULT_API_URL,
    DEFAULT_BACKLOG_PATH,
    DEFAULT_SAVE_FOLDER,
    DEFAULT_UNIT_LABEL,
    AppConfig,
    _deliver_readings,
    _prepare_payloads,
    main as ingest_main,
    parse_args,
)

main = ingest_main


if __name__ == "__main__":
    raise SystemExit(main())
