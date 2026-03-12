# Cafe Buddy

An AI-powered cafe ordering CLI featuring a conversational barista agent built on Gemini embeddings, FAISS vector search, and a LangChain tool-calling agent with full session memory.

## Features

- **Conversational Agent** — Natural language ordering powered by Google Gemini
- **Semantic Search** — FAISS vector search across drinks, cookies, and customizations
- **Dietary Conflict Resolution** — Detects conflicts and suggests compatible swaps automatically
- **Budget Management** — Soft three-zone budget system (safe / upsell / blocked)
- **Session Memory** — Agent remembers your preferences and basket across the conversation
- **Rich CLI** — Formatted terminal UI with slash commands

## Setup

1. **Clone repository & enter directory**
   ```bash
   git clone https://github.com/arjunnain17/cafe_buddy.git
   cd cafe_buddy
   ```

2. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   ```

4. **Create storage directory**
   ```bash
   mkdir storage
   ```

5. **Generate vector indexes**
   Run once initially, and re-run whenever you update any file in `data/`:
   ```bash
   python core/ingest.py
   ```

6. **Start the CLI**
   ```bash
   python app.py
   ```

## Usage

Just talk to Heer naturally:

```
You: something warm and sweet under ₹200
You: I'm vegan
You: I'll have the latte — large please
You: add a cookie too
You: /basket
You: checkout
```

Heer will search the menu, check dietary conflicts, track your budget, suggest upsells, and manage your basket automatically.

## Slash Commands

| Command | Description |
|---|---|
| `/basket` | Show current order and total |
| `/budget <amount>` | Set spending limit e.g. `/budget 500` |
| `/diet <preference>` | Set dietary preference e.g. `/diet vegan` |
| `/checkout` | Finalise order and print receipt |
| `/clear` | Clear basket — keeps budget and dietary settings |
| `/reset` | Clear everything including budget and dietary |
| `/verbose` | Toggle tool reasoning visibility |
| `/help` | Show all commands |
| `/quit` | Exit Cafe Buddy |


## Customizing the Menu

Edit the Python dictionaries in `data/drinks.py`, `data/cookies.py`, or `data/customizations.py` to add, remove, or change items. Then regenerate the indexes:

```bash
python core/ingest.py
```

## Requirements

- Python 3.10+
- Google Gemini API key (free tier supported)
- See `requirements.txt` for full dependency list