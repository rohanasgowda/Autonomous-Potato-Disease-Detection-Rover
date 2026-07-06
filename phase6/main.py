from __future__ import annotations

import argparse
import json

from phase3.app.utils.logging import configure_logging

from phase6.controller import Phase6WorkflowController
from phase6.settings import Phase6Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 6 Raspberry Pi workflow.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--phase4-config", default=None)
    parser.add_argument("--source-image", default=None, help="Use an existing image instead of the camera.")
    parser.add_argument("--farm-size-acres", type=float, default=None)
    parser.add_argument("--number-of-plants", type=int, default=None)
    parser.add_argument("--row-index", type=int, default=None)
    parser.add_argument("--plant-index", type=int, default=None)
    parser.add_argument("--country", default=None)
    parser.add_argument("--language", default=None)
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-telegram", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Phase6Settings.from_env(args.env_file, args.phase4_config)
    configure_logging(settings.phase3.log_level)
    controller = Phase6WorkflowController.from_settings(
        phase3_settings=settings.phase3,
        phase4_config=settings.phase4,
        model_path=settings.model_path,
        labels_path=settings.labels_path,
        capture_dir=settings.capture_dir,
        local_db_path=settings.local_db_path,
        camera_index=settings.camera_index,
        camera_warmup_seconds=settings.camera_warmup_seconds,
    )
    result = controller.run_scan(
        farm_size_acres=args.farm_size_acres or settings.farm_size_acres,
        number_of_plants=args.number_of_plants or settings.number_of_plants,
        country=args.country or settings.country,
        language=args.language or settings.language,
        row_index=args.row_index if args.row_index is not None else settings.row_index,
        plant_index=args.plant_index if args.plant_index is not None else settings.plant_index,
        source_image=args.source_image,
        sync_backend=not args.skip_backend,
        send_telegram=not args.skip_telegram,
    )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
