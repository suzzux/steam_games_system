# steam_games_system

Курсова робота з дисципліни «Бази даних та інформаційні системи» на тему «Відеоігри та Студії-розробники».
Розподілена система для каталогу ігор Steam: гексагональна архітектура (порти та адаптери) + CQRS + Polyglot Persistence.

| Сховище | Роль | Адаптер |
|---|---|---|
| MongoDB (шардований кластер, 2 шарди × 3 репліки) | основне сховище документа гри | `MongoAdapter`, `MongoShardAnalyticsAdapter` |
| Elasticsearch | повнотекстовий пошук, автодоповнення | `ElasticAdapter` |
| Neo4j | зв'язки гра–студія–дизайнер–платформа–жанр–рушій | `Neo4jAdapter` |
| Redis | кеш результатів пошуку/фільтрів, лічильники | `RedisAdapter` |
| Apache Kafka | події `game.events` для синхронізації сховищ | `KafkaEventPublisherAdapter`, `KafkaSyncConsumer` |

## Структура

```
src/
├── domain/            сутності, об'єкти-значення, доменні сервіси (QueryNormalizer, EngagementCalculator)
├── ports/             вхідні/вихідні порти та DTO
├── services/          use-case-и: команди, запити, синхронізація, map-reduce
├── adapters/
│   ├── driving/       GameAPIController, веб-UI (FastAPI + Jinja2), споживач Kafka, завантажувач датасету
│   └── driven/        MongoDB, шарди MongoDB, Elasticsearch, Neo4j, Redis, Kafka
├── entrypoints/       web, sync_worker, load_dataset, init_storage
├── bootstrap.py       створення адаптерів і сервісів (composition root)
└── config.py          налаштування зі змінних оточення
infra/mongo/           ініціалізація replica set'ів і шардування
tests/                 тести (mongomock + фейкові адаптери, без запуску баз)
docs/diagrams/         Python-код для чорно-білих схем звіту
```

## Запуск

```bash
cp .env.example .env                 # задати пароль Neo4j
docker compose up -d --build         # кластер MongoDB, ES, Neo4j, Redis, Kafka, web, sync-worker
# покласти оброблений датасет у data/steam_games_processed.csv, потім:
docker compose run --rm data-loader
```

Інтерфейс: http://localhost:8000 (каталог, картка гри, додавання/редагування, пошук, фільтр за зв'язками,
розподіл по шардах, map-reduce, моніторинг). JSON API: `/api/games`, `/api/search`, `/api/filter`,
`/api/analytics/map-reduce`, `/api/shards`, `/api/monitoring`. Документація API: http://localhost:8000/docs.

Перевірка шардування вручну:

```bash
docker compose exec mongos mongosh --eval 'sh.status()'
docker compose exec mongos mongosh steam --eval 'db.games.getShardDistribution()'
```

Для всієї системи потрібно приблизно 5–6 ГБ оперативної пам'яті Docker.

## Тести

```bash
pip install -r requirements-dev.txt
pytest
```

## Схеми для звіту

```bash
pip install -r docs/diagrams/requirements.txt   # потрібен також встановлений Graphviz (dot)
python docs/diagrams/make_all.py                # PNG з'являться в docs/diagrams/out/
```
