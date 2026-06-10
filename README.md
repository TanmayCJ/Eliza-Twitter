# Eliza Twitter/X Framework

An Eliza OS based Twitter/X bot framework for building autonomous AI agents that can generate posts, schedule tweets, reply to users, track interactions, and operate with character-driven behavior.

This project is designed for experimenting with AI-powered social agents, personality-based automation, and autonomous posting workflows on Twitter/X.

---

## Overview

Eliza Twitter Bot Framework provides a customizable foundation for creating AI agents that can interact on Twitter/X using structured character files, posting logic, interaction handling, and automated social behavior.

The framework can be used to build bots with distinct personalities, domain-specific opinions, scheduled posting behavior, reply handling, and context-aware social engagement.

---

## Features

* Autonomous Twitter/X posting
* Character-based AI behavior
* Custom personality and tone configuration
* Automated tweet generation
* Reply and interaction handling
* Latest tweet tracking
* Twitter client integration
* Database support for bot memory and state
* Modular TypeScript codebase
* Easily customizable for different bot themes

---

## Project Structure

```txt
Eliza-Twitter/
│
├── ElizaBots/
│   └── CarbonRant/
│       └── packages/
│           └── client-twitter/
│               └── src/
│                   ├── base.ts
│                   ├── checks.ts
│                   ├── database.ts
│                   ├── interactions.ts
│                   ├── latest_tweet.ts
│                   └── post.ts
│
├── .gitignore
└── README.md
```

---

## Tech Stack

* Eliza OS
* TypeScript
* Node.js
* Twitter/X API
* AI agent workflows
* Character-based prompt engineering
* Autonomous social automation

---

## Use Cases

This framework can be used to build:

* AI Twitter/X bots
* Character-based social agents
* Opinionated content bots
* Automated posting systems
* Brand/persona bots
* Research prototypes for agentic social media behavior
* Domain-specific AI commentators

---

## Example Bot Concepts

Some possible bots that can be built using this framework:

* Sustainability commentator bot
* Game development devlog bot
* AI research update bot
* Crypto/Web3 satire bot
* Tech news opinion bot
* Educational micro-content bot
* Fictional character social agent

---

## Core Modules

### `base.ts`

Contains the base Twitter client logic and shared setup for Twitter/X integration.

### `checks.ts`

Handles validation, safety checks, and posting conditions before actions are performed.

### `database.ts`

Manages persistence, stored state, bot memory, or tweet tracking depending on the configured setup.

### `interactions.ts`

Handles replies, mentions, user interactions, and engagement workflows.

### `latest_tweet.ts`

Tracks the latest posted tweet or recent Twitter/X activity.

### `post.ts`

Handles tweet generation, approval flow, scheduling, and posting logic.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/TanmayCJ/Eliza-Twitter.git
cd Eliza-Twitter
```

---

### 2. Install dependencies

Navigate into the bot package directory:

```bash
cd ElizaBots/CarbonRant
```

Install packages:

```bash
pnpm install
```

If you use npm instead:

```bash
npm install
```

---

### 3. Configure environment variables

Create a `.env` file and add your Twitter/X API credentials and other required bot configuration.

Example:

```env
TWITTER_USERNAME=
TWITTER_PASSWORD=
TWITTER_EMAIL=
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

Do not commit `.env` files to GitHub.

---

### 4. Run the bot

```bash
pnpm start
```

If using a specific character file:

```bash
pnpm start --character="characters/carbonrant.json"
```

---

## Character Configuration

The bot behavior is controlled through character configuration files. These files define the agent’s:

* Name
* Bio
* Style
* Tone
* Topics
* Personality
* Post examples
* Reply behavior
* Knowledge domain

This makes it easy to create multiple bots with different voices and objectives.

---

## Customization

To create a new Twitter/X bot:

1. Create or modify a character JSON file.
2. Update the bot’s personality, tone, and topics.
3. Configure posting frequency and interaction rules.
4. Add Twitter/X credentials in `.env`.
5. Run the bot locally or deploy it.

---

## Deployment

The framework can be deployed on:

* VPS
* Railway
* Render
* Docker-based server
* Cloud VM
* Local always-on machine

Recommended deployment improvements:

* Add Docker support
* Add GitHub Actions workflow
* Add process manager such as PM2
* Add logging and monitoring
* Add scheduled restart handling
* Store secrets securely using environment variables

---

## Security Notes

Before pushing or deploying:

* Never commit `.env`
* Never expose Twitter/X credentials
* Do not push API keys
* Review logs before making the repository public
* Use environment variables for all secrets

---

## Roadmap

* Add Dockerfile
* Add deployment guide
* Add character templates
* Add example bot configurations
* Add logging dashboard
* Add scheduling configuration
* Add analytics for tweets and replies
* Add safer approval flow before posting
* Add multi-bot support
* Add documentation for custom characters

---

## Repository Status

This repository is under active development and is intended as a customizable framework for building AI-powered Twitter/X agents using Eliza OS.

---

## Author

**Tanmay C Jain**

GitHub: [TanmayCJ](https://github.com/TanmayCJ)

---

## License

Add a license before public reuse or distribution.
