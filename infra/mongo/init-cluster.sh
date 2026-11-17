#!/bin/bash
# Ініціалізація шардованого кластера MongoDB (виконується одноразово контейнером mongo-init).
# 1) replica set конфігураційного сервера; 2) replica set кожного шарду (Primary + 2 Secondary);
# 3) додавання шардів через mongos і шардування колекції steam.games за хешем _id (game_id).
set -e

wait_for() {
  until mongosh --host "$1" --quiet --eval "db.adminCommand('ping').ok" >/dev/null 2>&1; do
    echo "Чекаю $1 ..."; sleep 2
  done
}

wait_primary() {
  until mongosh --host "$1" --quiet --eval "db.hello().isWritablePrimary" 2>/dev/null | grep -q true; do
    echo "Чекаю вибору Primary на $1 ..."; sleep 2
  done
}

for host in cfg1 shard1a shard1b shard1c shard2a shard2b shard2c; do wait_for "$host:27017"; done

echo "== Replica set конфігураційного сервера"
mongosh --host cfg1:27017 --quiet --eval '
try { rs.status(); print("cfgrs вже ініціалізовано") }
catch (e) { rs.initiate({_id: "cfgrs", configsvr: true, members: [{_id: 0, host: "cfg1:27017"}]}) }'

for s in 1 2; do
  echo "== Replica set rs-shard$s"
  mongosh --host "shard${s}a:27017" --quiet --eval "
  try { rs.status(); print('rs-shard$s вже ініціалізовано') }
  catch (e) { rs.initiate({_id: 'rs-shard$s', members: [
      {_id: 0, host: 'shard${s}a:27017', priority: 2},
      {_id: 1, host: 'shard${s}b:27017', priority: 1},
      {_id: 2, host: 'shard${s}c:27017', priority: 1}]}) }"
done

wait_primary cfg1:27017
wait_primary shard1a:27017
wait_primary shard2a:27017
wait_for mongos:27017

echo "== Додавання шардів і шардування колекції"
mongosh --host mongos:27017 --quiet /scripts/init-sharding.js
echo "Кластер готовий"
