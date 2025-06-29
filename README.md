# Connect 4 with Reinforcement Learning

This project is a Streamlit web application where you can play Connect 4 against an AI bot that learns and improves between games.

![Demo Screenshot](link-to-your-screenshot.png) <!-- You can add a screenshot later -->

---

## Features

- **Interactive UI:** A simple and clean web interface built with Streamlit.
- **Classic Game Logic:** Fully implemented Connect 4 game rules.
- **Two Learning Agents:**
  1.  **Q-Table Agent:** A classic reinforcement learning agent using a Q-table. It learns specific state-action values.
  2.  **DQN Agent:** A more advanced Deep Q-Network agent using TensorFlow that can generalize its learning to unseen board states.
- **Persistent Learning:** The agent's "brain" (`.pkl` or `.h5` file) is saved after each game, so its skill accumulates over time.

---

## Setup & Installation

This project is optimized for **Apple Silicon (M1/M2/M3) Macs**.

**1. Clone the repository:**
```bash
git clone https://github.com/<your-github-username>/connect4-rl.git
cd connect4-rl
```

**2. Install dependencies:**
```bash
pip install streamlit numpy tensorflow
```

**3. Run the application:**
```bash
streamlit run app.py
```
