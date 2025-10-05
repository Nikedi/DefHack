from pathlib import Path

from DefHack.sensors.audio.evaluate_dataset import FileMetadata, _balanced_shuffle


def _make_entry(label: str, index: int):
    metadata = FileMetadata(label=label, configuration=None, mission=None, extras={})
    return Path(f"{label.lower()}_{index}.wav"), metadata


def test_balanced_shuffle_includes_each_label_in_prefix():
    entries = [
        _make_entry("A", i) for i in range(4)
    ] + [
        _make_entry("B", i) for i in range(2)
    ]

    shuffled = _balanced_shuffle(entries, seed=123)

    assert len(shuffled) == len(entries)
    prefix_labels = {metadata.label for _, metadata in shuffled[:2]}
    assert prefix_labels == {"A", "B"}

    label_counts = {label: 0 for label in ("A", "B")}
    for _, metadata in shuffled:
        label_counts[metadata.label] += 1

    assert label_counts == {"A": 4, "B": 2}


def test_balanced_shuffle_single_label_is_stable():
    entries = [_make_entry("C", i) for i in range(3)]
    shuffled = _balanced_shuffle(entries, seed=99)

    labels = [metadata.label for _, metadata in shuffled]
    assert labels == ["C", "C", "C"]
