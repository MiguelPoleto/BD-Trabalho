import unittest

import mongomock

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


if __name__ == "__main__":
    unittest.main()
