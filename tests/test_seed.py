import unittest

import mongomock

from app import create_app
from seed import GAMES, PLAYERS, TEAMS, populate_database


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.database = mongomock.MongoClient().basquete_test

    def test_populates_demo_records_with_valid_references(self):
        counts = populate_database(self.database)

        self.assertEqual(counts, {"teams": len(TEAMS), "players": len(PLAYERS), "games": len(GAMES)})
        self.assertEqual(self.database.teams.count_documents({}), len(TEAMS))
        self.assertEqual(self.database.players.count_documents({}), len(PLAYERS))
        self.assertEqual(self.database.games.count_documents({}), len(GAMES))
        for player in self.database.players.find():
            self.assertIsNotNone(self.database.teams.find_one({"_id": player["team_id"]}))
        for game in self.database.games.find():
            self.assertIsNotNone(self.database.teams.find_one({"_id": game["home_team_id"]}))
            self.assertIsNotNone(self.database.teams.find_one({"_id": game["away_team_id"]}))

    def test_running_seed_again_does_not_duplicate_records(self):
        populate_database(self.database)
        populate_database(self.database)

        self.assertEqual(self.database.teams.count_documents({}), len(TEAMS))
        self.assertEqual(self.database.players.count_documents({}), len(PLAYERS))
        self.assertEqual(self.database.games.count_documents({}), len(GAMES))

    def test_demo_data_page_loads_seed_and_keeps_user_records(self):
        self.database.teams.insert_one({"name": "Equipe personalizada", "city": "Sao Paulo"})
        app = create_app(self.database)
        app.config["TESTING"] = True
        client = app.test_client()

        page = client.get("/tools/demo-data")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Carregar dados de demonstração".encode(), page.data)
        self.assertEqual(self.database.teams.count_documents({}), 1)

        response = client.post("/tools/demo-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("4 equipes, 20 jogadores e 8 partidas".encode(), response.data)
        self.assertEqual(self.database.teams.count_documents({}), len(TEAMS) + 1)
        self.assertEqual(self.database.players.count_documents({}), len(PLAYERS))
        self.assertEqual(self.database.games.count_documents({}), len(GAMES))
        self.assertIn("23/03/2026".encode(), client.get("/").data)
        self.assertIn("Ala-pivô".encode(), client.get("/players").data)
        for path in ("/teams", "/players", "/games", "/search"):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 200)

        client.post("/tools/demo-data")
        self.assertEqual(self.database.teams.count_documents({}), len(TEAMS) + 1)


if __name__ == "__main__":
    unittest.main()
