import os

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


TEAMS = [
    ("64a000000000000000000001", "Lobos de Curitiba", "Curitiba", "Carlos Mendes"),
    ("64a000000000000000000002", "Tubaroes de Santos", "Santos", "Renata Lima"),
    ("64a000000000000000000003", "Falcões de Campinas", "Campinas", "Paulo Rocha"),
    ("64a000000000000000000004", "Gigantes de Belo Horizonte", "Belo Horizonte", "Marina Costa"),
]

PLAYERS = [
    ("64b000000000000000000001", "Lucas Almeida", 7, "Armador", 0),
    ("64b000000000000000000002", "Pedro Nunes", 11, "Ala-armador", 0),
    ("64b000000000000000000003", "Rafael Souza", 23, "Ala", 0),
    ("64b000000000000000000004", "Bruno Martins", 34, "Ala-pivo", 0),
    ("64b000000000000000000005", "Mateus Oliveira", 50, "Pivo", 0),
    ("64b000000000000000000006", "Diego Santos", 3, "Armador", 1),
    ("64b000000000000000000007", "Felipe Costa", 8, "Ala-armador", 1),
    ("64b000000000000000000008", "Caio Ribeiro", 15, "Ala", 1),
    ("64b000000000000000000009", "Andre Carvalho", 21, "Ala-pivo", 1),
    ("64b00000000000000000000a", "Vitor Fernandes", 44, "Pivo", 1),
    ("64b00000000000000000000b", "Gustavo Pereira", 2, "Armador", 2),
    ("64b00000000000000000000c", "Enzo Rodrigues", 10, "Ala-armador", 2),
    ("64b00000000000000000000d", "Heitor Gomes", 18, "Ala", 2),
    ("64b00000000000000000000e", "Samuel Barbosa", 25, "Ala-pivo", 2),
    ("64b00000000000000000000f", "Arthur Dias", 41, "Pivo", 2),
    ("64b000000000000000000010", "Daniel Araujo", 1, "Armador", 3),
    ("64b000000000000000000011", "Leonardo Melo", 9, "Ala-armador", 3),
    ("64b000000000000000000012", "Thiago Cardoso", 17, "Ala", 3),
    ("64b000000000000000000013", "Murilo Teixeira", 30, "Ala-pivo", 3),
    ("64b000000000000000000014", "Breno Moreira", 55, "Pivo", 3),
]

GAMES = [
    ("64c000000000000000000001", 0, 1, 82, 76, "2026-03-01", "Arena Curitiba"),
    ("64c000000000000000000002", 2, 3, 91, 88, "2026-03-02", "Ginasio Campinas"),
    ("64c000000000000000000003", 1, 2, 74, 80, "2026-03-08", "Arena Santos"),
    ("64c000000000000000000004", 3, 0, 79, 85, "2026-03-09", "Arena BH"),
    ("64c000000000000000000005", 0, 2, 96, 89, "2026-03-15", "Arena Curitiba"),
    ("64c000000000000000000006", 1, 3, 87, 81, "2026-03-16", "Arena Santos"),
    ("64c000000000000000000007", 2, 0, 77, 83, "2026-03-22", "Ginasio Campinas"),
    ("64c000000000000000000008", 3, 1, 92, 86, "2026-03-23", "Arena BH"),
]


def populate_database(database):
    # IDs fixos tornam a carga repetivel sem duplicar os dados de demonstracao.
    for identifier, name, city, coach in TEAMS:
        database.teams.replace_one(
            {"_id": ObjectId(identifier)},
            {"name": name, "city": city, "coach": coach},
            upsert=True,
        )

    team_ids = [ObjectId(team[0]) for team in TEAMS]
    for identifier, name, number, position, team_index in PLAYERS:
        database.players.replace_one(
            {"_id": ObjectId(identifier)},
            {
                "name": name,
                "number": number,
                "position": position,
                "team_id": team_ids[team_index],
            },
            upsert=True,
        )

    for identifier, home_index, away_index, home_score, away_score, played_at, venue in GAMES:
        database.games.replace_one(
            {"_id": ObjectId(identifier)},
            {
                "home_team_id": team_ids[home_index],
                "away_team_id": team_ids[away_index],
                "home_score": home_score,
                "away_score": away_score,
                "played_at": played_at,
                "venue": venue,
            },
            upsert=True,
        )

    return {
        "teams": len(TEAMS),
        "players": len(PLAYERS),
        "games": len(GAMES),
    }


if __name__ == "__main__":
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=3000,
    )
    database = client[os.getenv("MONGODB_DATABASE", "basquete_db")]

    try:
        client.admin.command("ping")
        counts = populate_database(database)
    except PyMongoError as error:
        raise SystemExit(
            "Nao foi possivel conectar ao MongoDB. Inicie o servidor e confira MONGODB_URI."
        ) from error
    finally:
        client.close()

    print(
        "Dados de demonstracao carregados: "
        f"{counts['teams']} equipes, {counts['players']} jogadores e {counts['games']} partidas."
    )
