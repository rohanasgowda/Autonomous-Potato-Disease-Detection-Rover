from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from phase4.app.logging import configure_logging
from phase4.app.severity import SeverityAnalysis, analyze_severity_image, load_severity_config

LOGGER = logging.getLogger(__name__)


def _save_visualizations(image_path: str | Path, output_dir: Path, analysis: SeverityAnalysis) -> dict[str, str]:
    import cv2  # type: ignore

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    leaf_mask_path = output_dir / "leaf_mask.png"
    diseased_mask_path = output_dir / "diseased_mask.png"
    overlay_path = output_dir / "segmentation_overlay.png"

    overlay = image.copy()
    leaf_layer = image.copy()
    leaf_layer[analysis.leaf_mask > 0] = (0, 180, 0)
    overlay = cv2.addWeighted(overlay, 0.65, leaf_layer, 0.35, 0)
    disease_layer = overlay.copy()
    disease_layer[analysis.diseased_mask > 0] = (0, 0, 255)
    overlay = cv2.addWeighted(overlay, 0.75, disease_layer, 0.25, 0)

    cv2.imwrite(str(leaf_mask_path), analysis.leaf_mask)
    cv2.imwrite(str(diseased_mask_path), analysis.diseased_mask)
    cv2.imwrite(str(overlay_path), overlay)
    return {
        "leaf_mask": str(leaf_mask_path),
        "diseased_mask": str(diseased_mask_path),
        "overlay": str(overlay_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Phase 5 severity segmentation on one image.")
    parser.add_argument("--image", required=True, help="Input leaf image.")
    parser.add_argument("--output-dir", default="phase4/runs/severity_validation", help="Directory for masks and summary JSON.")
    parser.add_argument("--config", default=None, help="Optional JSON severity threshold config.")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_severity_config(args.config)
    output_dir = Path(args.output_dir)
    analysis = analyze_severity_image(args.image, config)
    paths = _save_visualizations(args.image, output_dir, analysis)

    summary = {
        "image_path": args.image,
        "leaf_pixel_count": analysis.result.leaf_pixel_count,
        "diseased_pixel_count": analysis.result.diseased_pixel_count,
        "severity": {
            "label": analysis.result.label,
            "infected_area_percent": analysis.result.infected_area_percent,
            "method": analysis.result.method,
        },
        "visualizations": paths,
    }
    summary_path = output_dir / "severity_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")
    LOGGER.info("Severity validation complete", extra={"_summary_path": str(summary_path)})
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
