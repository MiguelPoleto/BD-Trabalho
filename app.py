import os
from datetime import date

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from seed import populate_database

POSITIONS = ("Armador", "Ala-armador", "Ala", "Ala-pivo", "Pivo")
# Preserva os valores existentes no banco e exibe a grafia correta na interface.
POSITION_LABELS = {"Ala-pivo": "Ala-pivô", "Pivo": "Pivô"}


def create_app(database=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave-local-apenas-para-desenvolvimento")

    # Permite usar um banco de teste sem conectar ao MongoDB real.
    if database is None:
        client = MongoClient(
            os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            serverSelectionTimeoutMS=3000,
        )
        database = client[os.getenv("MONGODB_DATABASE", "basquete_db")]
        app.extensions["mongo_client"] = client

    teams = database["teams"]
    players = database["players"]
    games = database["games"]
    # Os campos *_team_id ligam jogadores e partidas às equipes cadastradas.

    @app.template_filter("date_br")
    def format_date(value):
        return date.fromisoformat(value).strftime("%d/%m/%Y")

    def all_teams():
        return list(teams.find().sort("name", 1))

    def team_labels():
        return {str(team["_id"]): team["name"] for team in all_teams()}

    def document_or_404(collection, identifier):
        try:
            # Converte o identificador da URL para o formato usado pelo MongoDB.
            object_id = ObjectId(identifier)
        except (InvalidId, TypeError):
            abort(404)
        document = collection.find_one({"_id": object_id})
        if document is None:
            abort(404)
        return document

    def parse_team_id(value):
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None

    def parse_score(value):
        score = int(value)
        if score < 0 or score > 300:
            raise ValueError
        return score

    @app.get("/")
    def index():
        latest_games = list(games.find().sort("played_at", -1).limit(5))
        return render_template(
            "index.html",
            team_count=teams.count_documents({}),
            player_count=players.count_documents({}),
            game_count=games.count_documents({}),
            latest_games=latest_games,
            team_labels=team_labels(),
        )

    @app.get("/tools/demo-data")
    def demo_data():
        return render_template(
            "demo_data.html",
            team_count=teams.count_documents({}),
            player_count=players.count_documents({}),
            game_count=games.count_documents({}),
        )

    @app.post("/tools/demo-data")
    def load_demo_data():
        counts = populate_database(database)
        flash(
            f"Dados prontos para a apresentação: {counts['teams']} equipes, "
            f"{counts['players']} jogadores e {counts['games']} partidas.",
            "success",
        )
        return redirect(url_for("demo_data"))

    @app.get("/teams")
    def list_teams():
        return render_template("teams.html", teams=all_teams(), edit_team=None)

    @app.post("/teams")
    def create_team():
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        coach = request.form.get("coach", "").strip()
        if not name or not city:
            flash("Nome e cidade são obrigatórios.", "error")
            return redirect(url_for("list_teams"))
        teams.insert_one({"name": name, "city": city, "coach": coach})
        flash("Equipe cadastrada.", "success")
        return redirect(url_for("list_teams"))

    @app.get("/teams/<identifier>/edit")
    def edit_team(identifier):
        team = document_or_404(teams, identifier)
        return render_template("teams.html", teams=all_teams(), edit_team=team)

    @app.post("/teams/<identifier>/edit")
    def update_team(identifier):
        document_or_404(teams, identifier)
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        coach = request.form.get("coach", "").strip()
        if not name or not city:
            flash("Nome e cidade são obrigatórios.", "error")
            return redirect(url_for("edit_team", identifier=identifier))
        teams.update_one(
            {"_id": ObjectId(identifier)},
            {"$set": {"name": name, "city": city, "coach": coach}},
        )
        flash("Equipe atualizada.", "success")
        return redirect(url_for("list_teams"))

    @app.post("/teams/<identifier>/delete")
    def delete_team(identifier):
        team = document_or_404(teams, identifier)
        team_id = team["_id"]
        # Mantém os relacionamentos válidos, impedindo remover equipes em uso.
        if players.find_one({"team_id": team_id}) or games.find_one(
            {"$or": [{"home_team_id": team_id}, {"away_team_id": team_id}]}
        ):
            flash("Não é possível remover uma equipe vinculada a jogadores ou partidas.", "error")
        else:
            teams.delete_one({"_id": team_id})
            flash("Equipe removida.", "success")
        return redirect(url_for("list_teams"))

    @app.get("/players")
    def list_players():
        roster = list(players.find().sort("name", 1))
        return render_template(
            "players.html",
            players=roster,
            teams=all_teams(),
            team_labels=team_labels(),
            positions=POSITIONS,
            position_labels=POSITION_LABELS,
            edit_player=None,
        )

    @app.post("/players")
    def create_player():
        name = request.form.get("name", "").strip()
        position = request.form.get("position", "")
        team_id = parse_team_id(request.form.get("team_id", ""))
        try:
            number = int(request.form.get("number", ""))
        except ValueError:
            number = -1
        if (
            not name
            or position not in POSITIONS
            or not 0 <= number <= 99
            or team_id is None
            or teams.find_one({"_id": team_id}) is None
        ):
            flash("Informe nome, camisa (0 a 99), posição e equipe válidos.", "error")
            return redirect(url_for("list_players"))
        players.insert_one(
            {
                "name": name,
                "number": number,
                "position": position,
                "team_id": team_id,
            }
        )
        flash("Jogador cadastrado.", "success")
        return redirect(url_for("list_players"))

    @app.get("/players/<identifier>/edit")
    def edit_player(identifier):
        player = document_or_404(players, identifier)
        return render_template(
            "players.html",
            players=list(players.find().sort("name", 1)),
            teams=all_teams(),
            team_labels=team_labels(),
            positions=POSITIONS,
            position_labels=POSITION_LABELS,
            edit_player=player,
        )

    @app.post("/players/<identifier>/edit")
    def update_player(identifier):
        document_or_404(players, identifier)
        name = request.form.get("name", "").strip()
        position = request.form.get("position", "")
        team_id = parse_team_id(request.form.get("team_id", ""))
        try:
            number = int(request.form.get("number", ""))
        except ValueError:
            number = -1
        if (
            not name
            or position not in POSITIONS
            or not 0 <= number <= 99
            or team_id is None
            or teams.find_one({"_id": team_id}) is None
        ):
            flash("Informe nome, camisa (0 a 99), posição e equipe válidos.", "error")
            return redirect(url_for("edit_player", identifier=identifier))
        players.update_one(
            {"_id": ObjectId(identifier)},
            {"$set": {"name": name, "number": number, "position": position, "team_id": team_id}},
        )
        flash("Jogador atualizado.", "success")
        return redirect(url_for("list_players"))

    @app.post("/players/<identifier>/delete")
    def delete_player(identifier):
        player = document_or_404(players, identifier)
        players.delete_one({"_id": player["_id"]})
        flash("Jogador removido.", "success")
        return redirect(url_for("list_players"))

    @app.get("/games")
    def list_games():
        return render_template(
            "games.html",
            games=list(games.find().sort("played_at", -1)),
            teams=all_teams(),
            team_labels=team_labels(),
            edit_game=None,
        )

    def game_form_data():
        home_team_id = parse_team_id(request.form.get("home_team_id", ""))
        away_team_id = parse_team_id(request.form.get("away_team_id", ""))
        played_at = request.form.get("played_at", "")
        venue = request.form.get("venue", "").strip()
        try:
            date.fromisoformat(played_at)
            home_score = parse_score(request.form.get("home_score", ""))
            away_score = parse_score(request.form.get("away_score", ""))
        except ValueError:
            return None
        if (
            home_team_id is None
            or away_team_id is None
            or home_team_id == away_team_id
            or teams.find_one({"_id": home_team_id}) is None
            or teams.find_one({"_id": away_team_id}) is None
        ):
            return None
        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_score": home_score,
            "away_score": away_score,
            "played_at": played_at,
            "venue": venue,
        }

    @app.post("/games")
    def create_game():
        game = game_form_data()
        if game is None:
            flash("Informe uma partida válida, com equipes diferentes e placares de 0 a 300.", "error")
            return redirect(url_for("list_games"))
        games.insert_one(game)
        flash("Partida cadastrada.", "success")
        return redirect(url_for("list_games"))

    @app.get("/games/<identifier>/edit")
    def edit_game(identifier):
        game = document_or_404(games, identifier)
        return render_template(
            "games.html",
            games=list(games.find().sort("played_at", -1)),
            teams=all_teams(),
            team_labels=team_labels(),
            edit_game=game,
        )

    @app.post("/games/<identifier>/edit")
    def update_game(identifier):
        document_or_404(games, identifier)
        game = game_form_data()
        if game is None:
            flash("Informe uma partida válida, com equipes diferentes e placares de 0 a 300.", "error")
            return redirect(url_for("edit_game", identifier=identifier))
        games.update_one({"_id": ObjectId(identifier)}, {"$set": game})
        flash("Partida atualizada.", "success")
        return redirect(url_for("list_games"))

    @app.post("/games/<identifier>/delete")
    def delete_game(identifier):
        game = document_or_404(games, identifier)
        games.delete_one({"_id": game["_id"]})
        flash("Partida removida.", "success")
        return redirect(url_for("list_games"))

    @app.get("/search")
    def search():
        kind = request.args.get("kind", "")
        results = []
        searched = False

        if kind == "roster":
            team_id = parse_team_id(request.args.get("team_id", ""))
            searched = True
            if team_id and teams.find_one({"_id": team_id}):
                results = list(players.find({"team_id": team_id}).sort("name", 1))
            else:
                flash("Selecione uma equipe válida.", "error")
        elif kind == "position":
            position = request.args.get("position", "")
            searched = True
            if position in POSITIONS:
                results = list(players.find({"position": position}).sort("name", 1))
            else:
                flash("Selecione uma posição válida.", "error")
        elif kind == "dates":
            start = request.args.get("start", "")
            end = request.args.get("end", "")
            searched = True
            try:
                date.fromisoformat(start)
                date.fromisoformat(end)
                if start > end:
                    raise ValueError
                # Datas ISO podem ser comparadas como texto neste formato.
                results = list(
                    games.find({"played_at": {"$gte": start, "$lte": end}}).sort("played_at", 1)
                )
            except ValueError:
                flash("Informe um intervalo de datas válido.", "error")
        elif kind == "team_games":
            team_id = parse_team_id(request.args.get("team_id", ""))
            searched = True
            if team_id and teams.find_one({"_id": team_id}):
                results = list(
                    games.find(
                        {"$or": [{"home_team_id": team_id}, {"away_team_id": team_id}]}
                    ).sort("played_at", -1)
                )
            else:
                flash("Selecione uma equipe válida.", "error")
        elif kind == "outcome":
            outcome = request.args.get("outcome", "")
            searched = True
            comparisons = {
                "home": {"$gt": ["$home_score", "$away_score"]},
                "away": {"$gt": ["$away_score", "$home_score"]},
            }
            if outcome in comparisons:
                # $expr compara o placar dos dois campos no proprio MongoDB.
                results = list(
                    games.find({"$expr": comparisons[outcome]}).sort("played_at", -1)
                )
            else:
                flash("Selecione um resultado válido.", "error")

        return render_template(
            "searches.html",
            kind=kind,
            results=results,
            searched=searched,
            teams=all_teams(),
            team_labels=team_labels(),
            positions=POSITIONS,
            position_labels=POSITION_LABELS,
        )

    return app


app = create_app()


if __name__ == "__main__":
    mongo_client = app.extensions["mongo_client"]
    try:
        mongo_client.admin.command("ping")
    except PyMongoError as error:
        raise SystemExit(
            "Não foi possível conectar ao MongoDB. Inicie o servidor e confira MONGODB_URI."
        ) from error
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
