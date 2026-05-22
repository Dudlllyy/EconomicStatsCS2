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
4. Start the tracker script first, then launch CS2.

## How to Run

**Option 1: The Executable File (For Convenience)**
You can use the compiled `.exe` file to run the tracker directly. This is the most convenient way, as it does not require you to install Python or any dependencies. Just download the `.exe` and double-click to launch!

**Option 2: From Source Code**
Ensure you have Python installed (Python 3.6+ recommended).
Run the script via terminal or command prompt:
```bash
python CS on browser.py
```
**Option 3: Web Version for Steam Overlay**

In addition to the standard console version, the project now includes a web-based script. It performs the exact same function — analyzing and predicting the enemy's economy — but outputs a clean interface to a local web page.

**The main feature:** You can use it directly in-game via the Steam Overlay!
    
**How to use:**
1. Run the web version Python script before your game. It will start a local server.
2. During the match, open the Steam Overlay (usually `Shift + Tab`).
3. Open the built-in Steam web browser.
4. Go to `http://127.0.0.1:3000`.

Now the economy tracker will always be right in front of you, eliminating the need to Alt-Tab out of CS2 or use a second monitor.

