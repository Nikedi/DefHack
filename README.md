# DefHack project


## Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for Python package management and development workflow. uv is a fast Python package manager and build tool that replaces pip and virtualenv for most tasks.

### Getting Started

1. **Install uv** (if you don't have it):
	```pwsh
	pip install uv
	```

2. **Install dependencies:**
	```pwsh
	uv pip install -r requirements.txt
	```
	Or, if using `pyproject.toml`:
	```pwsh
	uv pip install -r pyproject.toml
	```

3. **Add a new dependency:**
	```pwsh
	uv pip install <package>
	```
	This will update your lockfile automatically.

4. **Update dependencies:**
	```pwsh
	uv pip update
	```

### Development Workflow

- Make all changes in a feature branch.
- Use `uv` to manage dependencies and environments.
- Run your code and tests using the uv-managed environment.
- Keep `pyproject.toml` and `uv.lock` up to date.
- Before pushing, ensure all dependencies are locked and documented.

For more details, see the [uv documentation](https://github.com/astral-sh/uv).

### Debugging ingestion payloads

When running the live ingestion loop (`uv run python -m DefHack`), pass
`--debug-payloads` to print each JSON payload before it is sent to the API.
Backlog retries respect the flag as well, making it easy to confirm the exact
request body when diagnosing 4xx responses.

## Configuring sensor backends

The sensor pipeline ships with lightweight heuristics by default so it works
out-of-the-box.  To enable stronger models such as TinyYOLO (detection) or
FastSeg (segmentation), edit `DefHack/sensors/settings.py` and change the
`detection_backend` and `segmentation_backend` values.  Remember to install the
corresponding dependencies before switching backends.

### YOLOv8 image pipeline

The image sensor module includes a YOLOv8 + CLIP retrieval pipeline that can be
invoked directly from the command line:

```pwsh
uv run python -m DefHack.sensors.images path/to/image_or_folder --readings-json output.json
```

The command accepts one or more image paths or directories, applies the YOLOv8
detector, and (optionally) generates captions for each detection. Passing
`--readings-json` writes the structured results to a JSON file. You can also use
`--caption-top-k`, `--weights`, `--confidence`, and related flags to customise
the inference run. Run `uv run python -m DefHack.sensors.images --help` to see
the full option list.

### Output schema

Pipeline outputs are serialised as `SensorObservationIn` objects (defined in
`DefHack/sensors/SensorSchema.py`). Each observation captures a *class-level*
summary for an image:

| Field | Description |
| --- | --- |
| `time` | UTC timestamp when the image was analysed |
| `mgrs` | MGRS string supplied to the pipeline (defaults to `UNKNOWN`) |
| `what` | Target label (e.g. `person`, `car`, `airplane`) |
| `amount` | Number of detections for that label in the image |
| `confidence` | Average confidence (0-100) across detections of that label |
| `sensor_id` | Identifier reported via `--sensor-id` (defaults to `YOLOv8-Pipeline`) |
| `unit` | Measurement unit (currently `count`) |
| `observer_signature` | Observer value provided via `--observer` |
| `original_message` | Reserved for future text payloads (currently `null`) |

Because detections are grouped per label, you'll see at most one
`SensorObservationIn` entry for each class in a single image.

### Configuring YOLOv8 defaults

The `BackendSettings` dataclass in `DefHack/sensors/settings.py` exposes
configuration hooks for the YOLOv8 pipeline:

- `yolov8_weights`: override the Ultralytics weights identifier or path.
- `yolov8_caption_model`: change the CLIP retrieval model used for captions.
- `yolov8_device`: force the computation device (`"cuda"`, `"cpu"`, etc.).

These attributes can also be specified in the existing `extra` dictionary for
backward compatibility. After editing the settings module, subsequent pipeline
runs will transparently pick up the new defaults.


