from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

EXPECTED_SPLITS = {"train": 1034, "validation": 133, "test": 128}
EXPECTED_CLASSES = {"angular_leaf_spot", "bean_rust", "healthy"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _list_images(directory: Path) -> list[Path]:
    """Return the image files under `directory`, sorted so the order is stable."""
    return sorted(
        p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


# Milestone 6 check: this comment changes the code but not the quality report.
def validate_dataset(raw_root: Path) -> dict:
    """Validate the raw dataset and return a deterministic quality report.

    Core checks:
      1. required splits exist;
      2. exactly the expected classes exist in every split;
      3. expected image counts are present;
      4. every image can be fully decoded by Pillow (`Image.load()`);
      5. no split or class is empty.

    Any failed check raises, so the DVC stage stops. The report contains no
    timestamps because it is a DVC output.
    """
    if not raw_root.is_dir():
        raise FileNotFoundError(f"Raw data root {raw_root} does not exist.")

    # 1. Required splits exist.
    missing_splits = sorted(s for s in EXPECTED_SPLITS if not (raw_root / s).is_dir())
    if missing_splits:
        raise FileNotFoundError(f"Missing splits in {raw_root}: {missing_splits}")

    splits_report: dict[str, dict] = {}
    for split in sorted(EXPECTED_SPLITS):
        split_dir = raw_root / split

        # 2. Exactly the expected class directories (stray files are ignored).
        found_classes = {p.name for p in split_dir.iterdir() if p.is_dir()}
        if found_classes != EXPECTED_CLASSES:
            raise RuntimeError(
                f"Split '{split}' has wrong classes: "
                f"missing={sorted(EXPECTED_CLASSES - found_classes)}, "
                f"unexpected={sorted(found_classes - EXPECTED_CLASSES)}"
            )

        class_counts: dict[str, int] = {}
        for cls in sorted(EXPECTED_CLASSES):
            images = _list_images(split_dir / cls)

            # 5. No class is empty.
            if not images:
                raise RuntimeError(f"Class '{cls}' is empty in split '{split}'.")

            # 4. Pillow can decode every pixel, not just the header.
            for img_path in images:
                try:
                    with Image.open(img_path) as im:
                        im.load()
                except Exception as e:
                    raise OSError(f"Failed to decode image {img_path}: {e}") from e

            class_counts[cls] = len(images)

        # 3. Image counts match the course archive (also guarantees the split is not empty).
        n_images = sum(class_counts.values())
        if n_images != EXPECTED_SPLITS[split]:
            raise RuntimeError(
                f"Split '{split}' has {n_images} images, expected {EXPECTED_SPLITS[split]}."
            )

        splits_report[split] = {"images": n_images, "class_counts": class_counts}

    return {
        "status": "PASS",
        "classes": sorted(EXPECTED_CLASSES),
        "splits": splits_report,
        "total_images": sum(s["images"] for s in splits_report.values()),
    }


def main() -> None:
    report = validate_dataset(Path("data/raw"))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/data_quality.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
