import unittest

import mongomock

from app import create_app


class BasketballAppTests(unittest.TestCase):
    def setUp(self):
        self.database = mongomock.MongoClient().basquete_test
        self.app = create_app(self.database)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def create_team(self, name, city="Sao Paulo"):
        response = self.client.post(
            "/teams", data={"name": name, "city": city, "coach": "Tecnico"}
        )
        self.assertEqual(response.status_code, 302)
        return self.database.teams.find_one({"name": name})

    def create_player(self, name, team, position="Armador", number=7):
        return self.client.post(
            "/players",
            data={
                "name": name,
                "team_id": str(team["_id"]),
                "position": position,
                "number": number,
            },
        )

    def create_game(self, home, away, home_score=80, away_score=70, played_at="2026-03-10"):
        return self.client.post(
            "/games",
            data={
                "home_team_id": str(home["_id"]),
                "away_team_id": str(away["_id"]),
                "home_score": home_score,
                "away_score": away_score,
                "played_at": played_at,
                "venue": "Ginasio Central",
            },
        )

    def test_create_update_list_and_delete_team(self):
        team = self.create_team("Lobos")
        response = self.client.post(
            f"/teams/{team['_id']}/edit",
            data={"name": "Lobos do Sul", "city": "Curitiba", "coach": "Ana"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.database.teams.find_one({"_id": team["_id"]})["city"], "Curitiba")
        self.assertIn(b"Lobos do Sul", self.client.get("/teams").data)
        self.client.post(f"/teams/{team['_id']}/delete")
        self.assertIsNone(self.database.teams.find_one({"_id": team["_id"]}))

    def test_prevents_deleting_team_with_roster_or_games(self):
        home = self.create_team("Lobos")
        away = self.create_team("Feras")
        self.create_player("Joao", home)
        self.client.post(f"/teams/{home['_id']}/delete")
        self.assertIsNotNone(self.database.teams.find_one({"_id": home["_id"]}))
        self.database.players.delete_many({})
        self.create_game(home, away)
        self.client.post(f"/teams/{home['_id']}/delete")
        self.assertIsNotNone(self.database.teams.find_one({"_id": home["_id"]}))

    def test_player_crud_and_roster_and_position_searches(self):
        team = self.create_team("Lobos")
        response = self.create_player("Joao", team, "Armador", 7)
        self.assertEqual(response.status_code, 302)
        player = self.database.players.find_one({"name": "Joao"})
        self.assertIn(b"Joao", self.client.get(f"/search?kind=roster&team_id={team['_id']}").data)
        self.assertIn(b"Joao", self.client.get("/search?kind=position&position=Armador").data)
        response = self.client.post(
            f"/players/{player['_id']}/edit",
            data={
                "name": "Joao Silva",
                "number": 8,
                "position": "Ala",
                "team_id": str(team["_id"]),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.database.players.find_one({"_id": player["_id"]})["number"], 8)
        self.client.post(f"/players/{player['_id']}/delete")
        self.assertIsNone(self.database.players.find_one({"_id": player["_id"]}))

    def test_game_crud_and_date_team_and_outcome_searches(self):
        home = self.create_team("Lobos")
        away = self.create_team("Feras")
        response = self.create_game(home, away, 80, 70, "2026-03-10")
        self.assertEqual(response.status_code, 302)
        game = self.database.games.find_one({"home_team_id": home["_id"]})
        date_results = self.client.get("/search?kind=dates&start=2026-03-01&end=2026-03-31")
        team_results = self.client.get(f"/search?kind=team_games&team_id={away['_id']}")
        outcome_results = self.client.get("/search?kind=outcome&outcome=home")
        self.assertIn(b"Ginasio Central", date_results.data)
        self.assertIn(b"Ginasio Central", team_results.data)
        self.assertIn(b"Ginasio Central", outcome_results.data)
        response = self.client.post(
            f"/games/{game['_id']}/edit",
            data={
                "home_team_id": str(home["_id"]),
                "away_team_id": str(away["_id"]),
                "home_score": 65,
                "away_score": 75,
                "played_at": "2026-03-11",
                "venue": "Arena Sul",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.database.games.find_one({"_id": game["_id"]})["away_score"], 75)
        self.assertIn(
            b"Arena Sul", self.client.get("/search?kind=outcome&outcome=away").data
        )
        self.client.post(f"/games/{game['_id']}/delete")
        self.assertIsNone(self.database.games.find_one({"_id": game["_id"]}))

    def test_rejects_invalid_game_and_search_dates(self):
        home = self.create_team("Lobos")
        response = self.create_game(home, home)
        self.assertEqual(self.database.games.count_documents({}), 0)
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/search?kind=dates&start=2026-04-01&end=2026-03-01")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Informe um intervalo de datas válido.".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
