"""Веб-інтерфейс і JSON API (driving-адаптер).

Повний флоу для кожної сторінки:
браузер -> маршрут FastAPI -> GameAPIController -> вхідний порт (сервіс) -> вихідний порт (репозиторій/адаптер) -> БД
і назад: документ -> доменна сутність -> DTO -> HTML-шаблон.
"""
import dataclasses
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.adapters.driving.api_controller import GameAPIController

BASE_DIR = Path(__file__).parent
GROUP_FIELDS = [("genres", "Жанр"), ("platforms", "Платформа"), ("engine", "Рушій"),
                ("developers", "Розробник"), ("publishers", "Видавець"), ("game_designers", "Гейм-дизайнер")]
SORT_OPTIONS = [("release_desc", "Новіші"), ("release_asc", "Старіші"), ("price_asc", "Дешевші"),
                ("price_desc", "Дорожчі"), ("positive_desc", "Більше позитивних відгуків"),
                ("ccu_desc", "Більший піковий онлайн"), ("name_asc", "За назвою")]


def _opt_int(value) -> Optional[int]:
    return int(value) if value not in (None, "") else None


def _opt_float(value) -> Optional[float]:
    return float(value) if value not in (None, "") else None


def _split(value: str):
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def form_to_command(form) -> dict:
    """Поля HTML-форми -> словник для GameCreateCommandDTO (списки вводяться через кому)."""
    return {
        "name": form.get("name", ""),
        "price": float(form.get("price") or 0),
        "min_age": int(form.get("min_age") or 0),
        "release_date": form.get("release_date", ""),
        "short_description": form.get("short_description", ""),
        "detailed_description": form.get("detailed_description", ""),
        "engine": form.get("engine", ""),
        "genres": _split(form.get("genres")),
        "developers": _split(form.get("developers")),
        "publishers": _split(form.get("publishers")),
        "designers": _split(form.get("designers")),
        "platforms": _split(form.get("platforms")),
        "game_trailer": form.get("game_trailer", ""),
    }


def to_json(obj):
    return dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else obj


def create_app(controller: GameAPIController) -> FastAPI:
    app = FastAPI(title="Steam Games System")
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    def render(request: Request, name: str, status_code: int = 200, **context):
        return templates.TemplateResponse(request, name, context, status_code=status_code)

    @app.exception_handler(KeyError)
    async def not_found(request: Request, exc: KeyError):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": str(exc)}, status_code=404)
        return render(request, "error.html", 404, message=str(exc).strip("'\""))

    @app.exception_handler(ValueError)
    async def bad_request(request: Request, exc: ValueError):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        return render(request, "error.html", 400, message=str(exc))

    # ================================================================ HTML-сторінки
    @app.get("/", include_in_schema=False)
    def index():
        return RedirectResponse("/games")

    @app.get("/games", response_class=HTMLResponse)
    def games_page(request: Request, genre: str = "", platform: str = "", year_from: str = "", year_to: str = "",
                   max_price: str = "", name_prefix: str = "", sort: str = "release_desc", page: int = 1):
        params = dict(genre=genre or None, platform=platform or None, year_from=_opt_int(year_from),
                      year_to=_opt_int(year_to), max_price=_opt_float(max_price),
                      name_prefix=name_prefix or None, sort=sort, page=page)
        result = controller.list_games(params)
        query = {k: v for k, v in request.query_params.items() if k != "page" and v}
        return render(request, "games.html", page=result, facets=controller.facets(), filters=params,
                      raw=dict(request.query_params), query=query, sort_options=SORT_OPTIONS)

    @app.get("/games/new", response_class=HTMLResponse)
    def new_game_form(request: Request):
        return render(request, "game_form.html", game=None, action="/games/new")

    @app.post("/games/new")
    async def create_game(request: Request):
        game_id = controller.post_game(form_to_command(await request.form()))
        return RedirectResponse(f"/games/{game_id}", status_code=303)

    @app.get("/games/{game_id}", response_class=HTMLResponse)
    def game_page(request: Request, game_id: int):
        return render(request, "game.html", game=controller.get_game(game_id))

    @app.get("/games/{game_id}/edit", response_class=HTMLResponse)
    def edit_game_form(request: Request, game_id: int):
        return render(request, "game_form.html", game=controller.get_game(game_id),
                      action=f"/games/{game_id}/edit")

    @app.post("/games/{game_id}/edit")
    async def update_game(request: Request, game_id: int):
        controller.put_game(game_id, form_to_command(await request.form()))
        return RedirectResponse(f"/games/{game_id}", status_code=303)

    @app.post("/games/{game_id}/delete")
    def delete_game(game_id: int):
        controller.delete_game(game_id)
        return RedirectResponse("/games", status_code=303)

    @app.get("/search", response_class=HTMLResponse)
    def search_page(request: Request, q: str = ""):
        result = controller.search(q) if q.strip() else None
        return render(request, "search.html", q=q, result=result)

    @app.get("/filter", response_class=HTMLResponse)
    def filter_page(request: Request, platform: str = "", designer: str = ""):
        result = controller.filter(platform, designer) if platform and designer else None
        return render(request, "filter.html", platform=platform, designer=designer, result=result,
                      facets=controller.facets())

    @app.get("/shards", response_class=HTMLResponse)
    def shards_page(request: Request):
        return render(request, "shards.html", rows=controller.shard_distribution())

    @app.get("/analytics", response_class=HTMLResponse)
    def analytics_page(request: Request, group_by: str = "genres", year_from: str = "", year_to: str = "",
                       platform: str = "", top_n: int = 15, run: str = ""):
        params = dict(group_by=group_by, year_from=_opt_int(year_from), year_to=_opt_int(year_to),
                      platform=platform or None, top_n=top_n)
        result = controller.map_reduce(params) if run else None
        return render(request, "analytics.html", params=params, result=result, group_fields=GROUP_FIELDS,
                      facets=controller.facets())

    @app.get("/monitoring", response_class=HTMLResponse)
    def monitoring_page(request: Request):
        return render(request, "monitoring.html", data=controller.monitoring())

    # ================================================================ JSON API
    @app.get("/api/games")
    def api_list(genre: str = "", platform: str = "", year_from: str = "", year_to: str = "",
                 max_price: str = "", name_prefix: str = "", sort: str = "release_desc", page: int = 1,
                 page_size: int = 25):
        result = controller.list_games(dict(genre=genre or None, platform=platform or None,
                                            year_from=_opt_int(year_from), year_to=_opt_int(year_to),
                                            max_price=_opt_float(max_price), name_prefix=name_prefix or None,
                                            sort=sort, page=page, page_size=page_size))
        return dict(to_json(result), pages=result.pages)

    @app.post("/api/games", status_code=201)
    async def api_create(request: Request):
        return {"game_id": controller.post_game(await request.json())}

    @app.get("/api/games/{game_id}")
    def api_get(game_id: int):
        return to_json(controller.get_game(game_id))

    @app.put("/api/games/{game_id}")
    async def api_update(game_id: int, request: Request):
        return {"game_id": controller.put_game(game_id, await request.json())}

    @app.delete("/api/games/{game_id}")
    def api_delete(game_id: int):
        if not controller.delete_game(game_id):
            raise KeyError(f"Гру {game_id} не знайдено")
        return {"deleted": game_id}

    @app.get("/api/search")
    def api_search(q: str):
        return to_json(controller.search(q))

    @app.get("/api/autocomplete")
    def api_autocomplete(prefix: str):
        return controller.autocomplete(prefix)

    @app.get("/api/filter")
    def api_filter(platform: str, designer: str):
        return to_json(controller.filter(platform, designer))

    @app.get("/api/analytics/map-reduce")
    def api_map_reduce(group_by: str = "genres", year_from: str = "", year_to: str = "", platform: str = "",
                       top_n: int = 20):
        return to_json(controller.map_reduce(dict(group_by=group_by, year_from=_opt_int(year_from),
                                                  year_to=_opt_int(year_to), platform=platform or None,
                                                  top_n=top_n)))

    @app.get("/api/shards")
    def api_shards():
        return [to_json(r) for r in controller.shard_distribution()]

    @app.get("/api/monitoring")
    def api_monitoring():
        return to_json(controller.monitoring())

    return app
