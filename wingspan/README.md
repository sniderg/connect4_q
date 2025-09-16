# Wingspan AI Project

This directory houses plans and documentation for expanding the repository from the existing Connect 4 bot into a full Wingspan digital opponent and research environment. The goal is to model the tabletop game's rules faithfully, provide interfaces for experimentation, and enable training strong automated players.

## Objectives
- **Digitize the Rules**: Encode the complete Wingspan game state, legal actions, and deterministic state transitions so that a simulator can reproduce physical play.
- **Create Training Interfaces**: Expose the simulator through environment APIs suitable for reinforcement learning, search, and heuristic evaluation.
- **Develop Baseline Opponents**: Implement scripted strategies that mimic beginner and intermediate play to serve as sparring partners and data sources.
- **Enable Learning Agents**: Support imitation learning, reinforcement learning, and hybrid approaches that can learn effective Wingspan strategies from self-play and curated data.
- **Evaluate and Iterate**: Establish metrics, tournaments, and tooling to measure progress and debug complex interactions.

## Roadmap
1. **Rules Engine**
   - Represent player mats, birds, resources, bonus cards, round goals, and turn structure.
   - Define legal actions including playing birds, gaining food, laying eggs, drawing cards, and resolving triggered powers.
   - Implement deterministic transitions for habitat activations, predator hunts, caching, and round-end scoring, using seeded randomness for reproducibility.
2. **Environment API**
   - Wrap the simulator in an environment with `reset`, `step`, `observation`, `reward`, `done`, and `info` methods.
   - Design observation encodings that capture visible state and handle partial information.
   - Decide on reward schemes (victory points, intermediate shaping) suitable for various training algorithms.
3. **Baseline Bots & Heuristics**
   - Craft rule-based opponents emphasizing simple strategies (e.g., fast setups, resource engines).
   - Provide greedy evaluators for quick benchmarking and integration tests.
4. **Data & Imitation Learning**
   - Collect play traces from humans or scripted bots for supervised policy and value training.
   - Build tooling to visualize and inspect logged games.
5. **Reinforcement Learning & Self-Play**
   - Experiment with Monte Carlo Tree Search, PPO/A2C, DDQN, or hybrid techniques with action masking.
   - Address partial observability through belief modeling or recurrent networks.
   - Use curriculum strategies to scale from simplified to full game complexity.
6. **Evaluation & Tooling**
   - Track win rates, score distributions, goal completion, and action diversity across opponents.
   - Run tournaments between checkpoints and perform ablation studies on features and rewards.
   - Develop debugging UIs (CLI or web) to inspect game states and reproduce issues.

## Next Steps
- Finalize the data schema for bird cards, bonus cards, and goals.
- Draft unit tests for critical rule interactions before coding the simulator.
- Identify initial heuristic strategies to implement as baseline opponents.

As additional artifacts (design documents, data files, source code) are created for the Wingspan project, place them alongside this README within the `wingspan/` directory to keep all related resources organized.
