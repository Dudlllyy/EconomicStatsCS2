import json
import threading
import tkinter as tk
from http.server import BaseHTTPRequestHandler, HTTPServer

manual_saves = 0
last_processed_round = -1


game_state = {
    "t_score": 0, "ct_score": 0,
    "enemy": "CT", "bonus": 1400, "est_bank": 800,
    "last_winner": None, "eliminated": False, "is_pistol": True,
    "bomb_bonus": False
}



class GSIServer(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body.decode('utf-8'))
        self.analyze_state(data)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

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


            estimated_bank = 800
            loss_streak = 0
            last_winner_in_loop = None
            last_event = ""

            sorted_rounds = sorted([int(k) for k in round_wins.keys()])

            for r in sorted_rounds:

                if r == 13 or r == 25 or r == 31:
                    loss_streak = 0
                    estimated_bank = 800
                    last_winner_in_loop = None


                if r == 1 or r == 13 or r == 25:
                    spend = 800
                else:
                    if last_winner_in_loop == game_state["enemy"]:
                        spend = 1000
                    else:
                        if estimated_bank >= 4500:
                            spend = 4500
                        else:
                            spend = 1000

                estimated_bank -= spend
                if estimated_bank < 0: estimated_bank = 0

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
                    loss_streak += 1
                    if loss_streak > 4: loss_streak = 4
                    income = 1400 + (loss_streak * 500)

                    if game_state["enemy"] == "T" and win_event == "bombdefused":
                        income += 800
                else:

                    loss_streak -= 1
                    if loss_streak < 0: loss_streak = 0
                    income = 3250

                estimated_bank += income


                if estimated_bank > 16000: estimated_bank = 16000

                last_winner_in_loop = round_winner

            game_state["est_bank"] = estimated_bank
            game_state["bonus"] = 1400 + (loss_streak * 500)
            game_state["last_winner"] = last_winner_in_loop
            game_state["bomb_bonus"] = (game_state["enemy"] == "T" and last_event == "bombdefused")
            game_state["is_pistol"] = (game_state["t_score"] + game_state["ct_score"] in [0, 12, 24])

            recalculate_prediction()



def recalculate_prediction():
    s = game_state
    bank = s["est_bank"]
    save_text = f" (+{manual_saves} safe)" if manual_saves > 0 else ""

    if s["is_pistol"]:
        pred, color = "PISTOL ROUND ($800)", "#00ffff"
    elif bank >= 4500:
        if s["last_winner"] != s["enemy"]:
            pred, color = f"FULLBUY (all money: ~${bank})", "#00ff7f"
        else:
            pred, color = f"FULLBUY (Win streak)", "#00ff7f"
    elif bank >= 3000 and manual_saves >= 1:
        pred, color = f"DEFAULT BUY (Bank ~${bank}{save_text})", "#00ff7f"
    elif bank >= 2200:
        if s["bomb_bonus"]:
            pred, color = f"FORCE/BUY (bonus for bomb!)", "#ffd700"
        else:
            pred, color = f"LOW BUY (~${bank}{save_text})", "#ffd700"
    else:
        if manual_saves >= 2:
            pred, color = f"FORCE{save_text}", "#ffd700"
        elif s["eliminated"] and manual_saves == 0:
            pred, color = f"FULL ECO (~${bank})", "#ff4c4c"
        else:
            pred, color = f"ECO/FORCE (~${bank})", "#ff4c4c"

    def _update():
        lbl_score.config(text=f"Score: T [{s['t_score']}] - [{s['ct_score']}] CT")
        lbl_enemy.config(text=f"Enemy: {s['enemy']} | Lose-bonus: ${s['bonus']}")
        lbl_pred.config(text=pred, fg=color)
        lbl_saves.config(text=f"Safes: {manual_saves}")

    root.after(0, _update)


def run_server():
    server = HTTPServer(('127.0.0.1', 3000), GSIServer)
    server.serve_forever()


root = tk.Tk()
root.title("CS2 Predictor")
root.geometry("290x155")
root.attributes("-topmost", True)
root.overrideredirect(True)
root.configure(bg="#121212")


def start_move(event):
    root.x = event.x
    root.y = event.y


def do_move(event):
    x = root.winfo_x() + event.x - root.x
    y = root.winfo_y() + event.y - root.y
    root.geometry(f"+{x}+{y}")


drag_frame = tk.Frame(root, bg="#2a2a2a", height=20)
drag_frame.pack(fill="x", side="top")
drag_frame.bind("<Button-1>", start_move)
drag_frame.bind("<B1-Motion>", do_move)

btn_close = tk.Button(drag_frame, text="X", bg="#2a2a2a", fg="#ffffff", font=("Arial", 8, "bold"),
                      bd=0, activebackground="#ff4c4c", command=root.quit)
btn_close.pack(side="right", padx=5)

lbl_score = tk.Label(root, text="Waiting for game...", font=("Consolas", 11, "bold"), bg="#121212", fg="#aaaaaa")
lbl_score.pack(pady=(5, 0))

lbl_enemy = tk.Label(root, text="-", font=("Consolas", 10), bg="#121212", fg="#ffffff")
lbl_enemy.pack(pady=(0, 5))

lbl_pred = tk.Label(root, text="...", font=("Consolas", 11, "bold"), bg="#121212", fg="#ffffff")
lbl_pred.pack()


def add_save():
    global manual_saves
    if manual_saves < 5:
        manual_saves += 1
        recalculate_prediction()


def rem_save():
    global manual_saves
    if manual_saves > 0:
        manual_saves -= 1
        recalculate_prediction()


btn_frame = tk.Frame(root, bg="#121212")
btn_frame.pack(pady=(10, 0))

btn_minus = tk.Button(btn_frame, text="- Safe", bg="#ff4c4c", fg="white", bd=0, width=8, command=rem_save)
btn_minus.pack(side="left", padx=5)

lbl_saves = tk.Label(btn_frame, text="Safes: 0", font=("Consolas", 10), bg="#121212", fg="white")
lbl_saves.pack(side="left", padx=5)

btn_plus = tk.Button(btn_frame, text="+ Safe", bg="#00ff7f", fg="black", bd=0, width=8, command=add_save)
btn_plus.pack(side="left", padx=5)

threading.Thread(target=run_server, daemon=True).start()
root.mainloop()
