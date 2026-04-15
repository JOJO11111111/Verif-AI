# VerifAI 🔍

**AI-powered fact-checking for financial claims.**
Built for elders or people on their behalf to verify suspicious claims and protect against fraud. (Ponzi schemes, fake funds, social-media investment scams, elder financial exploitation).


CMU 14-789 · AI in Business Modeling · Course Project MVP

---

## What it does

Paste a  claim (e.g., *" On facebook there is a crypto fund called Doc Rock Company that pays 15% monthly dividends, guaranteed"*) and VerifAI returns a structured verdict:

- Overall trust score (0–100)
- Per-sub-claim verdict with confidence level
- Source citations (such as SEC, FINRA, official registries, regulator alerts)
- Red flags detected
- Plain-language reasoning summary
- Concrete recommendation

## How it works — Orchestration Premium architecture

VerifAI uses a **three-stage pipeline** that routes each task to the model best suited for it:

| Stage | Task | Model | Why |
|-------|------|-------|-----|
| 1 | Claim decomposition | Claude Sonnet 4.5 | Reasoning + structured output |
| 2 | Evidence retrieval | GPT-4o-mini + Tavily | Speed + cost-efficient retrieval |
| 3 | Verdict synthesis | Claude Sonnet 4.5 | Reasoning + explainability |

This is the **Orchestration Premium** business-model pattern: hidden multi-model routing creates value the user never has to think about.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/JOJO11111111/Verif-AI.git
cd verifai
```

### 2. Create a virtual environment & install dependencies

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your API keys

```bash
cp .env.example .env
# then edit .env and paste your keys
```

You'll need accounts at:
- [Anthropic Console](https://console.anthropic.com/)
- [OpenAI Platform](https://platform.openai.com/api-keys)
- [Tavily](https://app.tavily.com/)

### 4. Run

```bash
python run.py
```

The Streamlit app will open in your browser at `http://localhost:8501`.

---

## Project structure

```
verifai/
├── app.py              # Streamlit UI
├── pipeline.py         # Three-stage orchestration logic
├── prompts.py          # Prompt templates for each stage
├── run.py              # Launcher (loads .env, starts streamlit)
├── requirements.txt    # Python dependencies
├── .env.example        # Template for API keys
└── README.md
```

---

## Team

| Name | Andrew ID |
|------|-----------|
| Vy Tran | vtran |
| Samuel Green | slgreen |
| Gabriel Wimmer | gwimmer |
| Tiffany | tbao2 |

---

