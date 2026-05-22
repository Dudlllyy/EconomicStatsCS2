import json
from http.server import BaseHTTPRequestHandler, HTTPServer


manual_saves = 0
last_processed_round = -1

game_state = {
    "t_score": 0, "ct_score": 0,
    "enemy": "CT", "bonus": 1400, "est_bank": 800,
    "last_winner": None, "eliminated": False, "is_pistol": True,
    "bomb_bonus": False, "pred": "Waiting for match...", "color": "#ffffff"
}


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CS2 Predictor</title>
    <style>
        body { background-color: #0b0b0b; color: white; font-family: 'Consolas', monospace; text-align: center; padding-top: 15px; margin: 0; user-select: none; }
        .score { color: #aaaaaa; font-size: 18px; margin-bottom: 5px; font-weight: bold; }
        .enemy { font-size: 14px; margin-bottom: 15px; color: #dddddd; }
        .pred { font-size: 22px; font-weight: bold; margin-bottom: 20px; text-shadow: 0px 0px 5px rgba(0,0,0,0.8); }
        .btn { border: none; padding: 8px 15px; font-size: 16px; cursor: pointer; border-radius: 4px; font-weight: bold; transition: 0.1s; }
        .btn:active { transform: scale(0.95); }
        .btn-red { background: #ff4c4c; color: white; }
        .btn-green { background: #00ff7f; color: black; }
        .saves { margin: 0 15px; font-size: 16px; }
    </style>
</head>
<body>
    <div class="score" id="score">Waiting for match...</div>
    <div class="enemy" id="enemy">-</div>
    <div class="pred" id="pred">...</div>
    <div>
        <button class="btn btn-red" onclick="fetch('/rem_save')">- Save</button>
        <span class="saves" id="saves">Saves: 0</span>
        <button class="btn btn-green" onclick="fetch('/add_save')">+ Save</button>
    </div>

    <script>
        // The browser asks Python for new data every second
        setInterval(() => {
            fetch('/state')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('score').innerText = `Score: T [${data.t_score}] - [${data.ct_score}] CT`;
                    document.getElementById('enemy').innerText = `Enemy: ${data.enemy} | Loss Bonus: $${data.bonus} | Bank: ~$${data.est_bank}`;
                    const predEl = document.getElementById('pred');
                    predEl.innerText = data.pred;
                    predEl.style.color = data.color;
                    document.getElementById('saves').innerText = `Saves: ${data.saves}`;
                });
        }, 1000);
    </script>
</body>
</html>
"""


class GSIWebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass 


    def do_GET(self):
        global manual_saves
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))

        elif self.path == '/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            payload = {**game_state, "saves": manual_saves}
            self.wfile.write(json.dumps(payload).encode('utf-8'))

        elif self.path == '/add_save':
            if manual_saves < 5: manual_saves += 1
            recalculate_prediction()
            self.send_response(200)
            self.end_headers()

        elif self.path == '/rem_save':
            if manual_saves > 0: manual_saves -= 1
            recalculate_prediction()
            self.send_response(200)
            self.end_headers()


    def do_POST(self):
        if self.path == '/':
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)
            data = json.loads(body.decode('utf-8'))
            self.analyze_state(data)
            self.send_response(200)
            self.end_headers()

    def analyze_state(self, data):
        global manual_saves, last_processed_round, game_state

        if 'map' not in data or 'round' not in data or 'player' not in data: return

        phase = data['round'].get('phase')
        current_round = data['map'].get('round', 0)

        if current_round != last_processed_round and phase == 'freezetime':
            manual_saves = 0
            last_processed_round = current_round

        if phase == 'freezetime':
            my_team = data['player'].get('team')
            if not my_team: return

            game_state["enemy"] = "CT" if my_team == "T" else "T"
            game_state["t_score"] = data['map'].get('team_t', {}).get('score', 0)
            game_state["ct_score"] = data['map'].get('team_ct', {}).get('score', 0)

            round_wins = data['map'].get('round_wins', {})
            estimated_bank, loss_streak = 800, 0
            last_winner_in_loop, last_event = None, ""

            sorted_rounds = sorted([int(k) for k in round_wins.keys()])
            for r in sorted_rounds:
                if r in [13, 25, 31]:
                    loss_streak, estimated_bank, last_winner_in_loop = 0, 800, None

                spend = 800 if r in [1, 13, 25] else (
                    1000 if last_winner_in_loop == game_state["enemy"] else (4500 if estimated_bank >= 4500 else 1000))
                estimated_bank = max(0, estimated_bank - spend)

                win_event = round_wins[str(r)].lower()
                last_event = win_event

                if win_event.startswith('t_win') or win_event == 'target_bombed':
                    round_winner = "T"
                elif win_event.startswith('ct_win') or win_event in ['bombdefused', 'target_saved']:
                    round_winner = "CT"
                else:
                    continue

                game_state["eliminated"] = win_event.endswith('elimination')

                if round_winner != game_state["enemy"]:
                    loss_streak = min(4, loss_streak + 1)
                    income = 1400 + (loss_streak * 500)
                    if game_state["enemy"] == "T" and win_event == "bombdefused": income += 800
                else:
                    loss_streak = max(0, loss_streak - 1)
                    income = 3250

                estimated_bank = min(16000, estimated_bank + income)
                last_winner_in_loop = round_winner

            game_state.update({
                "est_bank": estimated_bank, "bonus": 1400 + (loss_streak * 500),
                "last_winner": last_winner_in_loop,
                "bomb_bonus": (game_state["enemy"] == "T" and last_event == "bombdefused"),
                "is_pistol": (game_state["t_score"] + game_state["ct_score"] in [0, 12, 24])
            })
            recalculate_prediction()


def recalculate_prediction():
    s = game_state
    bank = s["est_bank"]
    save_txt = f" (+{manual_saves} save(s))" if manual_saves > 0 else ""

    if s["is_pistol"]:
        pred, color = "PISTOL ROUND ($800)", "#00ffff"
    elif bank >= 4500:
        if s["last_winner"] != s["enemy"]:
            pred, color = f"FULL BUY (Cushion: ~${bank})", "#00ff7f"
        else:
            pred, color = "FULL BUY (Win Streak)", "#00ff7f"
    elif bank >= 3000 and manual_saves >= 1:
        pred, color = f"BUY (~${bank}{save_txt})", "#00ff7f"
    elif bank >= 2200:
        if s["bomb_bonus"]:
            pred, color = "FORCE/BUY (Bomb Bonus!)", "#ffd700"
        else:
            pred, color = f"WEAK BUY (~${bank}{save_txt})", "#ffd700"
    else:
        if manual_saves >= 2:
            pred, color = f"FORCE{save_txt}", "#ffd700"
        elif s["eliminated"] and manual_saves == 0:
            pred, color = f"PURE ECO (~${bank})", "#ff4c4c"
        else:
            pred, color = f"ECO / FORCE (~${bank})", "#ff4c4c"

    game_state["pred"] = pred
    game_state["color"] = color


server = HTTPServer(('127.0.0.1', 3000), GSIWebHandler)
print("Server started open the Steam browser and go to http://127.0.0.1:3000")
server.serve_forever()