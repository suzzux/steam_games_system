"""data-generator: завантаження обробленого датасету в MongoDB.

python -m src.entrypoints.load_dataset --csv data/steam_games_processed.csv [--limit 1000] [--batch 1000]
"""
import argparse
import logging

from src.bootstrap import build_adapters, setup_logging
from src.config import Settings
from src.services.command_service import GameCommandService
from src.adapters.driving.dataset_loader import DatasetLoader

log = logging.getLogger("steam_app")


def main():
    parser = argparse.ArgumentParser(description="Завантаження датасету Steam у MongoDB")
    parser.add_argument("--csv", default="data/steam_games_processed.csv")
    parser.add_argument("--batch", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    settings = Settings()
    setup_logging(settings)
    c = build_adapters(settings)
    loader = DatasetLoader(GameCommandService(c.repository, c.publisher, c.cache), batch_size=args.batch)
    report = loader.load(args.csv, limit=args.limit)
    log.info("Готово: оброблено %d, збережено %d, з помилками %d", report.processed, report.saved, report.failed)
    for error in report.errors:
        log.warning("Пропущено рядок: %s", error)


if __name__ == "__main__":
    main()
