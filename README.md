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

### Acoustic drone detection pipeline

The acoustic sensor module analyses either recorded WAV files or synthetic
rotor simulations to detect blade-pass frequency (BPF) signatures. Importing
`DefHack.sensors.audio` automatically registers the `acoustic_drone_bpf`
algorithm with the shared `SensorSchema` factory.

- **Simulated capture** (generates an observation from physics-based rotor noise):

```pwsh
uv run python -m DefHack.sensors.audio --report
```

- **Analyse an existing recording**:

```pwsh
uv run python -m DefHack.sensors.audio path/to/recording.wav --place 35VLG8472571866 --report
```

Each run prints the derived `SensorObservationIn` payload and, when
`--report` is used, writes a human-readable text summary to
`DefHack/sensors/audio/data/processed/`. The pipeline is configurable via
`DefHack/sensors/audio/config.yaml`; override keys (sampling rate, FFT window,
harmonic count, etc.) or pass runtime flags such as `--rpm` and `--blades`
to tune the physics model for different rotorcraft.

Just like the image pipeline, the CLI forwards results as
`SensorObservationIn` records. By default they are written to
`DefHack/sensors/audio/predictions.json`; pass `--readings-json` to choose a
different destination or `--no-summary` to suppress console output when
running in batch mode. Forwarded readings carry the unit `"Alpha Company"`
and their `what` field is automatically prefixed with `"TACTICAL:"` for
downstream routing consistency.

#### Evaluating the UAV Propeller Anomaly dataset

Download the [UAV Propeller Anomaly Audio Dataset](https://github.com/tiiuae/UAV-Propeller-Anomaly-Audio-Dataset)
and extract it locally. Then run the evaluator to batch-process the WAV files:

```pwsh
uv run python -m DefHack.sensors.audio.evaluate_dataset C:/path/to/UAV-Propeller-Anomaly-Audio-Dataset --output reports/propeller_eval.csv
```

The command prints aggregate detection statistics per class and writes a CSV
with per-file fundamentals, harmonic counts, SNR, and textual descriptions. Use
`--format json` or `--max-files` to switch formats or sample subsets, and add
`--reports` to keep individual text summaries alongside the dataset. Inputs are
shuffled in a label-balanced order so capped runs still include every category;
set `--seed` for deterministic shuffling. A progress bar is displayed by
default; pass `--no-progress` when running in non-TTY environments.

To quickly review the results visually, run the helper script (requires
`matplotlib`):

```pwsh
uv run python tests/visualize_propeller_eval.py --show
```

This loads `reports/propeller_eval.csv`, generates a summary PNG at
`reports/propeller_eval_summary.png`, and plots detection rate and confidence
per class alongside a scatter of detected blade-pass frequencies.

#### Sweeping detector parameters with ESC-50 and MLSP

Use the parameter sweep utility to benchmark multiple acoustic tuning presets
against a positive (MLSP) and negative (ESC-50) dataset in one pass:

```pwsh
uv run python -m DefHack.sensors.audio.parameter_sweep --max-positive 500 --max-negative 500 --quiet
```

By default the script searches for `MLSP_2022_Real_Data/real_data` and
`ESC-50/audio` relative to the repository, iterating across a grid of
`prominence_ratio`, `min_bpf_hz`, `max_bpf_hz`, `num_harmonics`, and
`noise_floor_db` values. Results are written to `reports/parameter_sweep.csv`
and summarised in the console.

Add `--prominence-ratio`, `--min-bpf`, `--max-bpf`, `--harmonics`,
`--noise-floor`, or repeated `--override KEY=VALUE` flags to expand the grid or
force constant overrides. The evaluator reuses the balanced shuffling logic
from `evaluate_dataset`, so capped runs remain representative and reproducible
with `--seed`.


