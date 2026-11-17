"""Запуск веб-інтерфейсу та JSON API: python -m src.entrypoints.web"""
import os

import uvicorn

from src.bootstrap import build_adapters, build_controller, setup_logging
from src.config import Settings
from src.adapters.driving.web.app import create_app


def main():
    settings = Settings()
    setup_logging(settings)
    app = create_app(build_controller(build_adapters(settings)))
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
