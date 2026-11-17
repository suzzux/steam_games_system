// Виконується через mongos (маршрутизатор).
const existing = db.adminCommand({ listShards: 1 }).shards.map(s => s._id);

if (!existing.includes("rs-shard1")) sh.addShard("rs-shard1/shard1a:27017,shard1b:27017,shard1c:27017");
if (!existing.includes("rs-shard2")) sh.addShard("rs-shard2/shard2a:27017,shard2b:27017,shard2c:27017");

// Менший розмір чанка (за замовчуванням 128 МБ), щоб на ~250 тис. документів
// утворилось кілька десятків чанків і було видно роботу балансувальника.
db.getSiblingDB("config").settings.updateOne(
  { _id: "chunksize" }, { $set: { value: 32 } }, { upsert: true });

sh.enableSharding("steam");

// Хешоване шардування за _id (= game_id). Для порожньої колекції MongoDB одразу
// створює початкові чанки і розподіляє їх між шардами.
const meta = db.getSiblingDB("config").collections.findOne({ _id: "steam.games" });
if (!meta) {
  sh.shardCollection("steam.games", { _id: "hashed" });
  print("steam.games зашардовано за { _id: 'hashed' }");
} else {
  print("steam.games вже зашардовано: " + tojson(meta.key));
}

sh.status();
