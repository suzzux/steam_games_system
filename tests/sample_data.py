"""Невеликий набір тестових ігор (імітують рядки датасету; ті самі ігри, що й у тестовому запуску розділу 3)."""
from src.ports.dtos import GameCreateCommandDTO

ROWS = [
    dict(game_id=95184, name="Rebound VR", price=9.99, min_age=0, release_date="Mar 3, 2019",
         platforms=["PC", "PS5"], designers=["Jacob Davis"], genres=["Action", "Indie", "Sports"],
         developers=["Quake Business"], publishers=["Caffinated Cauldron"], engine="Godot",
         positive=120, negative=30, peak_ccu=15, detailed_description="Fast VR ball sport arena"),
    dict(game_id=81506, name="FALLEN ANGELS", price=0.0, min_age=16, release_date="Nov 12, 2021",
         platforms=["Nintendo Switch 2", "Wii U"], designers=["Jacob Davis"], genres=["Action", "Sci-Fi"],
         developers=["Spell Helix"], publishers=["dReal"], engine="Unity",
         positive=40, negative=10, peak_ccu=230, detailed_description="Space shooter with angels"),
    dict(game_id=1117, name="Captain Forever Remix", price=14.99, min_age=0, release_date="Feb 18, 2016",
         platforms=["PS5", "Xbox Series X/S"], designers=["Jennifer Stephens"], genres=["Action", "Indie"],
         developers=["FlirtFit Studios"], publishers=["Enlight Software Limited", "Retroism"], engine="Unity",
         positive=800, negative=100, peak_ccu=60, detailed_description="Build your space ship and shooter battles"),
    dict(game_id=19338, name="Emily Wants To Play", price=4.99, min_age=12, release_date="Dec 10, 2015",
         platforms=["Nintendo Switch 2", "PC", "Xbox Series X/S"], designers=["Emily Newman"],
         genres=["Action", "Adventure", "Casual", "Indie", "Simulation", "Strategy"],
         developers=["Ropeat Team"], publishers=["dReal"], engine="UbiArt Framework",
         positive=5000, negative=900, peak_ccu=700, detailed_description="Horror night in a house"),
    dict(game_id=192662, name="Patterna Environmental: Situation", price=0.0, min_age=0, release_date="",
         platforms=["PS5", "PC", "Xbox One", "Xbox Series X/S"], designers=["Keith Griffin"],
         genres=["Casual", "Free To Play", "Indie"], developers=["Ropeat Team"], publishers=["SlippyfopGames"],
         engine="Giants Engine", positive=3, negative=1, peak_ccu=1, detailed_description="Puzzle patterns"),
]


def commands():
    result = []
    for row in ROWS:
        row = dict(row)
        result.append(GameCreateCommandDTO(short_description=row["detailed_description"][:30], **row))
    return result
