
# MCP-Based Dual AI Agent Conversation via MCP Servers

## Assignment 6: Cops-and-Robbers Pursuit Between Autonomous Agents in a Partially Observable Environment

# Course Title: AI Agent Communication Through MCP Servers


# 1. Introduction and Academic Context

This lecture is entirely dedicated to explaining an advanced assignment in the Computer Science Department at the University of Haifa.

The assignment focuses on **AI Agent Orchestration** and serves as a regular course assignment. In addition, it offers a **bonus opportunity of up to 10 points toward the final project**, which is submitted separately.

The primary objective is to move students beyond thinking about a **single intelligent agent operating in a static environment** and toward the broader world of **distributed multi-agent systems**, where multiple autonomous entities must make complex real-time decisions while coordinating with one another.

Dr. Yoram Segal emphasizes that the focus of the assignment has shifted away from optimizing a specific decision-making algorithm and toward:

* System engineering
* Orchestration challenges
* Natural-language communication between remote agents

Since Reinforcement Learning is not a prerequisite for the course, the use of sophisticated learning algorithms is presented only as an **academic extension and recommendation**, rather than a mandatory requirement.

Students are expected to demonstrate complex orchestration capabilities by constructing a complete **Pipeline** that enables two AI agents to successfully play against each other while coping with:

* Partial observability
* Game-board uncertainty
* Environmental uncertainty

---

# 2. Main Task Definition and Orchestration Challenge

The primary assignment is to design, implement, and operate a complete end-to-end game pipeline that enables two autonomous AI agents:

* **Cop**
* **Thief**

to participate in a dynamic pursuit game on a two-dimensional grid.

The orchestration process requires both agents to:

### 1. Interpret one another's natural-language messages

### 2. Infer information about the opponent's location using only partial observations

### 3. Translate these insights into physical movements on the game grid

The primary success criterion is **the communication and orchestration capabilities of the agent pair**, not the quality of the underlying game strategy.

Each team must present a fully autonomous sequence of games played between its own pair of agents (Cop and Thief), managed through MCP servers from initialization to final automated report generation, without any manual intervention.

---

# 3. Game Rules, Grid Structure, and Scoring System

## 3.1 Sub-Games and Full Games

The framework distinguishes between two levels:

### Sub-Game

A single pursuit round limited to a maximum of **25 moves**.

Players take turns.

Typically:

1. The Thief moves first.
2. The Cop moves second.
3. The cycle repeats.

During each turn, a player may either:

* Move to another cell
* Perform a special action

---

### Full Game

A complete game consists of **6 consecutive sub-games**.

The results of all sub-games are accumulated and reported collectively at the end of the series.

---

## 3.2 Game Board

The default board is a:

**5 × 5 two-dimensional grid**

The architecture must support dynamic board sizes through configuration files rather than hard-coded values.

Each cell possesses coordinates.

The Cop and the Thief begin in board locations that may be:

* Randomly assigned
* Strategically chosen

Movement is allowed in **all directions**, including diagonals.

The game effectively functions as a finite-state machine in which every move changes the board state.

---

## 3.3 Winning Conditions and Barrier Placement

### Cop Victory

The Cop wins when it reaches the exact cell currently occupied by the Thief.

This represents a successful capture.

---

### Thief Victory

The Thief wins if it survives all **25 moves** without the Cop entering its cell.

---

### Barrier Placement

Instead of moving, the Cop may place a **Barrier**.

The barrier is placed in the cell currently occupied by the Cop.

Effects:

* The Cop does not move during that turn.
* The selected cell becomes impassable.
* Neither the Cop nor the Thief may enter the blocked cell afterward.
* The barrier behaves similarly to a wall or board boundary.

Restrictions:

* The Cop may place at most **5 barriers per sub-game**.
* The Thief cannot place barriers.

---

# 3.4 Scoring System

Scores are calculated separately for each sub-game.

### Table 1: Scoring for a Single Sub-Game

| Sub-Game Result | Cop Score | Thief Score |
| --------------- | --------- | ----------- |
| Cop Wins        | 20        | 5           |
| Thief Wins      | 5         | 10          |

The maximum possible score for a team across a complete game series is:

* **90 points** (playing as Cop)
* plus **30 points** (playing as Thief)

The minimum possible score is determined by the outcomes of all six sub-games.

---

# 3.5 Progressive Sanity Checks

To facilitate integration testing and prevent late-stage technological failures, teams are encouraged to perform sanity checks on progressively larger grid sizes.

### Table 2: Recommended Sanity Check Stages

| Stage | Grid Size | Validation Goal                                                                                 | Complexity |
| ----- | --------- | ----------------------------------------------------------------------------------------------- | ---------- |
| 1     | 2×2       | Algorithmic sanity checks, basic Pipeline integration, and message-passing verification         | Very Low   |
| 2     | 3×2 / 3×3 | Testing convergence of coordination mechanisms, hyperparameter tuning, and failure detection    | Medium     |
| 3     | 4×3 / 4×4 | Evaluating ambiguity caused by partial observations; initial distances exceed visibility radius | High       |
| 4     | 5×5       | Final evaluation, graph generation, and analysis of complete game results                       | Maximum    |

---

# 4. MCP Server Architecture and Natural Language Communication

## 4.1 Two Servers, Free-Form Language, and Tools

The **Model Context Protocol (MCP)** is an open standard designed to connect Large Language Models (LLMs) with external tools, resources, and information sources.

The orchestration architecture consists of:

* One MCP server for the Cop
* One MCP server for the Thief

A fundamental principle of the assignment is that agents **must not communicate through a rigid protocol containing direct numeric positions**.

Instead, communication must occur through **free-form natural language**.

During each turn, an agent generates textual messages describing:

* Intentions
* Local observations
* Inferences
* Possible deception attempts

The receiving agent uses MCP-exposed tools together with its LLM to:

1. Read the message
2. Analyze its meaning
3. Update its internal belief state
4. Select its next action

Each MCP server is built using **FastMCP** and exposes tools that support:

* Position validation
* Message transmission
* Message reception

---

## 4.2 MCP Server vs. MCP Client

A critical architectural distinction:

The **LLM is not hosted inside the MCP server**.

The MCP server merely exposes:

* Tools
* Resources
* Prompts

The actual orchestration logic resides in the **MCP Client**, which the students implement.

The client is responsible for:

* Managing the dialogue
* Maintaining state
* Deciding when to invoke tools

### Workflow

1. The client sends a query to the LLM.
2. The LLM decides that a tool call is needed.
3. The client invokes the appropriate MCP tool.
4. The result is returned to the LLM.
5. The interaction cycle continues.

Thus, the MCP server functions only as an interface layer, while the MCP client acts as the orchestrator.

---

# 5. MCP Server Deployment

## Stage 1 – Local Execution

Initially, teams should run both MCP servers locally on separate ports.

The goals are:

* Verify communication between agents
* Verify game-engine integration
* Confirm end-to-end functionality

---

## Stage 2 – Cloud Deployment

After the local pipeline operates correctly, the MCP servers should be deployed to a public cloud environment, such as:

* Prefect Cloud
* Similar distributed platforms

---

## Security and Authentication

A token-based authentication mechanism is mandatory.

Examples include:

* Authentication Tokens
* Token Revocation support

This prevents unauthorized third-party access.

---

## Critical Networking and Security Considerations

The MCP server URLs must be publicly reachable from the Internet.

They must not be blocked by:

* Firewalls
* Organizational networks
* Corporate network policies

It is therefore **not recommended** to deploy or test servers from workplaces or heavily restricted institutional networks.

Each team must ultimately provide:

* One public URL for the Cop MCP server
* One public URL for the Thief MCP server

---

# 6. LLM Architecture: Three Possible Approaches

Even when MCP servers are hosted in the cloud, an LLM is still required.

Three architectural approaches are supported.

---

# 6.1 Approach 1: Public Cloud LLM API (Recommended)

This is the simplest and recommended approach.

Rather than exposing a local model, the MCP Client communicates directly with a public cloud model such as:

* OpenAI
* Anthropic
* Google (Gemini)

using an API key.

### Operation

1. The game engine sends an API request.
2. The cloud provider returns an LLM response.
3. The response may contain a Tool Call.
4. The MCP Client routes the request to the MCP server.
5. The tool result is returned to the model.

### Advantages

* Stable deployment
* Minimal infrastructure maintenance
* No firewall complications
* No need to expose personal hardware
* Very low operating costs because interactions are short

Many teams can complete the project using free or low-cost API tiers.

---

# 6.2 Approach 2: Secure Exposure of Local Ollama Models

Ollama runs local models and, by default, listens on port:

```text
127.0.0.1:11434
```

Directly exposing Ollama to the public Internet without protection is considered a serious security risk.

Therefore, if a team wishes to run its own local LLM while exposing it externally, a secure tunneling solution is required.

Possible solutions include:

### ngrok

* Creates a public HTTPS endpoint
* Supports Traffic Policies
* Supports Basic Authentication
* Allows controlled access to the local Ollama instance

### Localtonet

Similar to ngrok, but provides a convenient management interface and HTTP authentication capabilities.

### Nginx Reverse Proxy

For a full engineering solution:

* Nginx serves as a reverse proxy in front of Ollama.
* SSL termination is provided using Let's Encrypt / Certbot.
* Authentication can be enforced via `.htpasswd`.
* Local firewalls such as UFW or nftables can block direct access to Ollama's port.

---

# 6.3 Approach 3: Hybrid Architecture (Recommended for Safe Local Development)

Rather than exposing the local LLM to the Internet, teams may choose a hybrid architecture.

In this configuration:

* The game engine (orchestrator) runs locally.
* The LLM runs locally via Ollama.
* Only the MCP servers are hosted in the cloud.

### Architecture

```text
Local Machine
 ├── Game Engine
 ├── MCP Client
 └── Ollama (localhost:11434)

Cloud
 ├── Cop MCP Server
 └── Thief MCP Server
```

The game engine communicates with the local Ollama instance via:

```text
localhost:11434
```

without exposing the model externally.

Whenever communication with an MCP server is required, the game engine performs an outbound HTTPS request to the cloud-hosted server.

### Why is this safer?

Outbound HTTPS connections generally do not require opening inbound firewall ports.

As a result:

* The local machine remains protected behind its firewall.
* The local IP address is not publicly exposed.
* The LLM remains private.
* Only the MCP servers are publicly accessible.

This architecture combines:

* Local inference
* Strong security
* Simpler networking

and is therefore recommended for local development.

---

# 7. Recommended Reinforcement Learning Approach: Simple Q-Table

The use of **Reinforcement Learning (RL)** is optional.

Teams that prefer not to use RL may implement decision-making through:

* Heuristics
* Manhattan distance calculations
* Rule-based systems
* Decision trees
* Prompt-engineering techniques

However, Dr. Segal recommends **Tabular Q-Learning** as a lightweight approach that can improve agent performance without requiring deep neural networks.

---

## 7.1 State, Action, and Reward

Three fundamental RL concepts are used:

### State (s)

Represents the current situation of the agent.

Examples:

* Current location
* Known barriers
* Estimated opponent location

---

### Action (a)

Represents a decision taken by the agent.

Examples:

* Move North
* Move South
* Move East
* Move West
* Move Diagonally
* Place Barrier

---

### Reward (r)

Measures the desirability of an outcome.

Dr. Segal illustrates this concept using a treasure-hunting drone:

* Each move consumes fuel → small negative reward.
* Falling into a pit → large negative reward.
* Finding the treasure → large positive reward.

Over many episodes, the agent learns which states and actions are valuable.

---

## 7.2 Q-Table and the Bellman Equation

A Q-table stores the expected quality of each action in each state.

Rows correspond to states:

```text
s
```

Columns correspond to actions:

```text
a
```

Each cell contains:

```text
Q(s,a)
```

which estimates the long-term cumulative reward.

The agent follows an **Epsilon-Greedy policy**, balancing:

* Exploration
* Exploitation

The Q-values are updated using the Bellman Equation.

### Bellman Update Rule

[
Q(s,a)
======

Q(s,a)
+
\alpha
\left[
r
+
\gamma
\max_{a'}
Q(s',a')
--------

Q(s,a)
\right]
]

Where:

### α (Learning Rate)

Controls how strongly new information affects existing knowledge.

Typical values:

```text
0.01 – 0.5
```

---

### γ (Discount Factor)

Determines the importance of future rewards.

Typical range:

```text
0 – 1
```

---

### max Q(s', a')

Represents the highest expected future reward available from the next state.

---

### Example Q-Learning Update Code

```python
import numpy as np

# 5x5 grid -> 25 states
num_states = 25
num_actions = 4

q_table = np.zeros((num_states, num_actions))

learning_rate = 0.1
discount_factor = 0.9

def update_q_table(
    state,
    action,
    reward,
    next_state,
    done
):

    best_next_q = (
        0.0 if done
        else np.max(q_table[next_state])
    )

    td_target = (
        reward
        + discount_factor * best_next_q
    )

    td_error = (
        td_target
        - q_table[state, action]
    )

    q_table[state, action] += (
        learning_rate * td_error
    )
```

This approach enables agents to improve their behavior over time through trial and error without requiring computationally expensive deep-learning frameworks.

---

# 8. Automated Email Reporting and JSON Report Structure

At the conclusion of all sub-games, the Cop agent is expected to automatically invoke a reporting function that sends a single summary email to:

```text
rmisegal+uoh26b@gmail.com
```

### Recommended Technology

The assignment recommends using:

* Gmail API
* Google API Client

instead of traditional SMTP authentication.

---

## Why Use Token-Based Authentication?

Dr. Segal explains that storing a permanent username and password is less secure because stolen credentials can be abused indefinitely.

Google's OAuth mechanism issues temporary access tokens that:

* Have limited lifetimes
* Have limited permissions
* Can be revoked

making them significantly safer.

---

### Additional Rules

#### Rule 1 — Technical Failures

If a sub-game terminates because of a technical failure:

```text
Technical Loss
```

the game is considered invalid and must be rerun until the required six valid sub-games have been completed.

---

#### Rule 2 — Email Content

The email body must contain:

**Only the JSON report**

No free-form text should be included.

This allows automated parsing and grading.

---

# 8.1 Internal Game JSON Report

This report is used for games played between agents belonging to the same team.

It must contain:

* Team information
* GitHub repository
* MCP server URLs
* Game results
* Total scores

### Internal Report Structure

```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/marl-cop-thief",
  "cop_mcp_url": "https://cop-mcp-alpha.prefect.run",
  "thief_mcp_url": "https://thief-mcp-alpha.prefect.run",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": {
    "cop": 90,
    "thief": 40
  }
}
```

---

# 8.2 Inter-Group Bonus Competition JSON Report

This report is used when two different teams compete against each other in the cloud.

It contains:

* Information about both teams
* Four MCP server URLs
* Two GitHub repositories
* Combined scoring results
* Bonus claims

```json
{
  "report_type": "bonus_game",
  "groups": {
    "group_1": "Team-Alpha",
    "group_2": "Team-Beta"
  },
  ...
}
```

The remainder of the JSON structure should be preserved exactly as specified in the assignment.

---
# 9. Configuration File

As part of sound software engineering practices, **hard-coding game parameters is strictly prohibited**.

All configurable values must be centralized in a dedicated configuration file such as:

```text
config.json
```

or

```text
config.yaml
```

---

### Table 3: Configuration Parameters

| Parameter            | Description                                         | Default Value |
| -------------------- | --------------------------------------------------- | ------------- |
| `grid_size`          | Dimensions of the game grid                         | `[5,5]`       |
| `max_moves`          | Maximum number of moves per sub-game                | `25`          |
| `num_games`          | Number of sub-games in a complete series            | `6`           |
| `max_barriers`       | Maximum number of barriers the Cop may place        | `5`           |
| `scoring.cop_win`    | Score awarded to the Cop after a successful capture | `20`          |
| `scoring.thief_win`  | Score awarded to the Thief after successful evasion | `10`          |
| `scoring.cop_loss`   | Score awarded to the Cop when the Thief escapes     | `5`           |
| `scoring.thief_loss` | Score awarded to the Thief when captured            | `5`           |

---

### Example Configuration File

```json
{
  "grid_size": [5, 5],
  "max_moves": 25,
  "num_games": 6,
  "max_barriers": 5,

  "scoring": {
    "cop_win": 20,
    "thief_win": 10,
    "cop_loss": 5,
    "thief_loss": 5
  }
}
```

This configuration should be loaded dynamically by the application at runtime.

---

# 10. Submission Requirements and Scientific README Report

The submission consists of two primary deliverables:

## 1. Public GitHub Repository

The repository must contain:

* All source code
* Documentation
* Configuration files
* Deployment scripts
* Any supporting assets

---

## 2. Scientific README Report

A comprehensive scientific report named:

```text
README.md
```

must be located in the root directory of the repository.

The report should be written in a professional academic style and include the following sections.

---

## Formal Modeling

The pursuit problem should be modeled as a:

### Decentralized Partially Observable Markov Decision Process (Dec-POMDP)

The report should formally define:

* The mathematical tuple
* State space
* Action space
* Observation space
* Transition function
* Reward function

The generic Dec-POMDP tuple is:

[
\langle
n,
S,
{A_i},
P,
R,
{\Omega_i},
O,
\gamma
\rangle
]

Where:

| Symbol | Meaning                    |
| ------ | -------------------------- |
| n      | Number of agents           |
| S      | State space                |
| Ai     | Action space of each agent |
| P      | Transition function        |
| R      | Reward function            |
| Ωi     | Observation space          |
| O      | Observation function       |
| γ      | Discount factor            |

---

### Example State Space

The state space may include:

```text
(
Cop_Position,
Thief_Position,
Barrier_Locations
)
```

---

## Orchestration Challenges Analysis

The report should provide a detailed discussion of:

### Natural Language Communication Challenges

Including:

* Ambiguity
* Misinterpretation
* Incomplete observations
* Deception attempts

---

### Coordination Mechanisms

Explain how the agents achieve mutual understanding despite the absence of a predefined communication protocol.

Topics may include:

* Prompt design
* Shared conventions
* Belief updating
* Information extraction

---

## Visualization and Experimental Evidence

The report should include:

### Learning Curves

If Q-Learning was used:

* Reward progression
* Win-rate progression
* Exploration decay

---

### GUI Screenshots

Screenshots demonstrating:

* Agent movement
* Barrier placement
* Captures
* Overall gameplay

---

### MCP Communication Logs

Evidence that the MCP servers function correctly, including:

* Tool invocations
* Message exchanges
* Successful server communication

Both local and cloud deployments should be documented.

---

# 11. Inter-Group Bonus Competition

Beyond the mandatory requirement of running games between agents belonging to the same team, students may participate in an optional inter-group competition.

---

## Competition Requirements

Two teams:

1. Deploy their MCP servers to the cloud.
2. Run a complete competitive match.
3. Play six sub-games.
4. Independently submit identical reports.

Both teams must agree on:

* Results
* Scores
* JSON report contents

---

## 11.1 Role Swapping

### First Three Sub-Games

```text
Team A Cop
vs
Team B Thief
```

---

### Last Three Sub-Games

```text
Team B Cop
vs
Team A Thief
```

This ensures fairness.

---

## 11.2 Bonus Scoring Rules

### Winner

The team with the highest cumulative score receives:

```text
10 Bonus Points
```

---

### Loser

The losing team receives:

```text
7 Bonus Points
```

---

### Tie

In the event of a perfect tie:

```text
5 Bonus Points
```

are awarded to each team.

---

### Multiple Opponents

Teams are encouraged to compete against multiple groups.

The final bonus score is computed as the average across all valid competitions.

---

### Example

Suppose a team participates in two competitions:

Competition 1:

```text
Win → 10 points
```

Competition 2:

```text
Loss → 7 points
```

Final bonus:

[
\frac{10+7}{2}=8.5
]

Therefore:

```text
Final Bonus = 8.5 points
```

---

### Invalid Reports

Any disagreement between teams regarding:

* Results
* Scores
* JSON reports

invalidates the competition.

Both teams receive:

```text
0 Bonus Points
```

for that series.

---

# 12. Recommended Engineering Roadmap

To maximize the likelihood of producing a working system within the available time, the following implementation order is recommended.

### Table 4: Recommended Development Priorities

| Stage | Required Activity                                                   | Functional Focus             |
| ----- | ------------------------------------------------------------------- | ---------------------------- |
| 1     | Implement game rules, movement, barriers, and capture detection     | Core game logic              |
| 2     | Build two MCP servers capable of mutual position validation         | Basic MCP infrastructure     |
| 3     | Connect agents and game engine on localhost                         | Complete local execution     |
| 4     | Develop a strategy (heuristic, distance-based, or Q-table)          | Decision-making              |
| 5     | Replace rigid coordinate exchange with free-form text communication | Natural language integration |
| 6     | Build a GUI displaying agents and barriers in real time             | Graphical user interface     |
| 7     | Deploy MCP servers to the cloud while addressing security concerns  | Distributed cloud deployment |
| 8     | Implement automated JSON reporting through Gmail API                | Automated reporting          |

---

# 13. Key Takeaways

## Infrastructure Before Strategy

The primary educational value of the assignment lies in orchestration:

* Building two autonomous AI agents
* Creating MCP-based communication
* Establishing distributed coordination

The actual game outcome is secondary.

---

## Natural Language Instead of Rigid Protocols

Agents are independent entities.

As long as they successfully understand each other, the specific internal implementation is irrelevant.

The focus is on effective communication rather than predefined message formats.

---

## Formal Dec-POMDP Modeling

The assignment naturally maps onto a Dec-POMDP framework because:

* Multiple agents exist.
* Observations are partial.
* Decisions are sequential.
* Rewards are accumulated over time.

---

## Separation of Responsibilities

The architecture follows a clear separation:

### MCP Server

Responsible only for exposing:

* Tools
* Resources
* Prompts

### MCP Client (Orchestrator)

Responsible for:

* Reasoning
* Decision making
* LLM interaction
* Tool invocation

---

## Gradual Progression

The recommended progression is:

```text
Localhost
→ Cloud Deployment
→ Inter-Team Competition
```

while addressing:

* Domains
* Authentication tokens
* Tunneling
* Cybersecurity

---

## Three LLM Deployment Options

1. Public Cloud APIs (OpenAI, Anthropic, Gemini)
2. Securely Exposed Local Ollama
3. Hybrid Architecture (Recommended)

---

## Security and Automation

Modern security practices should be followed:

* OAuth tokens instead of passwords
* Token revocation mechanisms
* Secure APIs

Automated reporting through Gmail API enables fully autonomous system operation.

---

## Soft Skills

The assignment also emphasizes:

* Team collaboration
* Project planning
* Working under uncertainty
* Time management

The dynamics resemble concepts from Game Theory, particularly the Prisoner's Dilemma, where coordination and trust become essential factors in success.

---

