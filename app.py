from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from pathlib import Path

app = Flask(__name__)
CORS(app)

def load_players():
    file_path = Path('players.json')
    try:
        with open(file_path, 'r') as file:
            players = json.load(file)
        return players
    except Exception as e:
        return {"error": str(e)}

def load_question_types():
    file_path = Path('question_types.txt')
    try:
        with open(file_path, 'r') as file:
            question_types = [line.strip() for line in file.readlines()]
        return question_types
    except Exception as e:
        return {"error": str(e)}

game_state = {
    "available_players": [],
    "already_selected": [],
    "round_number": 1,
    "selected_players": [],
    "question_types": load_question_types()
}

@app.route('/start_game', methods=['GET'])
def start_game():
    players = load_players()
    if "error" in players:
        return jsonify({"error": "Failed to load players."}), 500
    if "error" in game_state["question_types"]:
        return jsonify({"error": "Failed to load question types."}), 500
    game_state["available_players"] = players
    game_state["already_selected"] = []
    game_state["round_number"] = 1
    game_state["selected_players"] = random.sample(players, 2)
    game_state["already_selected"].extend(game_state["selected_players"])
    question_type = random.choice(game_state["question_types"])
    return jsonify({"round_number": game_state["round_number"], "players": game_state["selected_players"], "question_type": question_type})

@app.route('/make_choice', methods=['POST'])
def make_choice():
    data = request.json
    question_type = data.get("question_type")
    choice_index = int(data.get("choice")) - 1
    correct_choice_index = validate_choice(game_state["selected_players"], question_type)
    
    if correct_choice_index == -1:
        return jsonify({"message": "Invalid question type."}), 400
    
    if choice_index == correct_choice_index:
        correct_player = game_state["selected_players"][correct_choice_index]
        new_opponent = choose_new_opponent()
        if not new_opponent:
            return jsonify({"message": "Congratulations, you've gone through all players!"}), 200
        game_state["selected_players"] = [correct_player, new_opponent]
        game_state["already_selected"].append(new_opponent)
        game_state["round_number"] += 1
        question_type = random.choice(game_state["question_types"])
        return jsonify({"message": "Correct choice!", "round_number": game_state["round_number"], "players": game_state["selected_players"], "question_type": question_type})
    else:
        return jsonify({"message": "Incorrect choice. Game over."}), 200

def validate_choice(selected_players, question_type):
    for player in selected_players:
        if question_type not in player:
            return -1  # Question type not a valid key in player data
    # Assuming the question_type directly corresponds to a key in the player data
    correct_choice_index = 0 if float(selected_players[0][question_type]) >=float(selected_players[1][question_type]) else 1
    return correct_choice_index

def choose_new_opponent():
    new_pool = [player for player in game_state["available_players"] if player not in game_state["already_selected"]]
    if not new_pool:
        return None
    return random.choice(new_pool)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
