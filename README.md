# CS2 Economy Tracker

Console-based Python application for tracking and predicting the enemy team's economy in Counter-Strike 2. 

## Features
* **Loss Bonus Tracking:** Automatically calculates dynamic loss bonuses ($1400 to $3400).
* **Save/Survival Logic:** Adjusts expected enemy economy based on how many players saved their equipment.
* **Buy Prediction:** Predicts whether the enemy will Full Buy, Force Buy, or Eco in the upcoming round.
* **Bomb Plant Bonus:** Accounts for the $800 bonus when the losing team plants the bomb.

## Game State Integration Setup

To allow the program to read live match data, you need to add the GSI configuration file to your CS2 directory:

1. Locate your local CS2 game files.
2. Copy the `gamestate_integration_economy.cfg` file from this repository.
3. Paste it into the following directory:
   `C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\`
   *(Note: Make sure to drop it in the `game\csgo\cfg` folder, NOT the old `csgo\cfg` folder)*
4. Start the Python tracker script first, then launch CS2.

## How to Run
Ensure you have Python installed (Python 3.6+ recommended).
Run the script via terminal or command prompt:

Usage

After each round, the program will ask you:

    Did the enemy team win? (y/n)

    How many enemy players survived/saved? (0-5)

    Was the bomb planted? (y/n - only if they lost the round)

Based on this input, the tool will estimate their current balance and predict their buy for the next round.


---

### 3. Файл игнорирования (`.gitignore`)
Чтобы не засорять репозиторий кэшем Python.

```text
# Python cache
__pycache__/
*.py[cod]
*$py.class

# IDE configurations
.idea/
.vscode/
*.swp

```bash
python CS.py


