# XAIagent: AnthroKit Validation Study

**Loan pre-assessment chatbot implementation for validating personality-adaptive anthropomorphism in XAI contexts.**

## Overview

This application validates the AnthroKit framework by testing three levels of anthropomorphism (None, Low, High) in a loan application scenario, with optional personality-based adaptation.

## Study Design

**3 Anthropomorphism Levels × 2 Adaptation Modes = 6 Conditions (N=60-90):**

### Anthropomorphism Levels
- **NoA (None)**: Formal, system-focused (warmth=0.00, empathy=0.00, formality=0.85)
- **LowA (Low)**: Professional, minimal warmth (warmth=0.25, empathy=0.15, formality=0.70)
- **HighA (High)**: Conversational, personified (warmth=0.70, empathy=0.55, formality=0.55)

### Adaptation Modes
- **Fixed**: Base preset values only
- **Personalized**: TIPI-based adjustments (±0.30 range)

### Six Experimental Conditions

| Condition | Anthropomorphism | Personalization | Entry Point |
|-----------|-----------------|-----------------|-------------|
| 1 | None | Fixed | `app_nonanthro.py` |
| 2 | None | Personalized | `app_nonanthro_personalize.py` |
| 3 | Low | Fixed | `app_condition_5.py` |
| 4 | Low | Personalized | `app_condition_5_personality.py` |
| 5 | High | Fixed | `app_v1.py` |
| 6 | High | Personalized | `app_v1_personality.py` |

### Dependent Measures
- Social Presence (adapted from Gefen & Straub, 2004)
- Trust in AI system
- Satisfaction ratings
- Interaction logs (tone configurations, generation metadata)

## Project Structure

```
XAIagent/
├── src/
│   ├── app_nonanthro.py           # NoA Fixed condition
│   ├── app_nonanthro_personalize.py # NoA Personalized condition
│   ├── app_condition_5.py         # LowA Fixed condition
│   ├── app_condition_5_personality.py # LowA Personalized condition
│   ├── app_v1.py                  # HighA Fixed condition
│   ├── app_v1_personality.py      # HighA Personalized condition
│   ├── ab_config.py               # A/B testing configuration
│   ├── loan_assistant.py          # Loan assessment logic
│   ├── natural_conversation.py    # LLM integration (GPT-4o-mini)
│   └── interaction_logger.py      # GitHub API logging
├── .streamlit/
│   └── secrets.toml.example       # Configuration template
├── config/
│   ├── system_prompt_high.txt     # HighA system prompt
│   └── system_prompt_low.txt      # LowA/NoA system prompt
├── data/
│   └── adult.data                 # UCI Adult dataset
├── models/                         # Trained classifiers
├── assets/                         # UI resources
└── tests/                          # Unit tests
```

## Setup

**1. Install AnthroKit package:**
```bash
cd /home/kudzy/Projects/AnthroKit
pip install -e .
```

**2. Install dependencies:**
```bash
cd XAIagent
pip install -r requirements.txt
```

**3. Configure environment:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Add your OPENAI_API_KEY and GITHUB_TOKEN to secrets.toml
```

## Running Study Conditions

**NoA Conditions:**
```bash
# NoA Fixed
ANTHROKIT_ANTHRO=none PERSONALITY_ADAPTATION=disabled streamlit run src/app_nonanthro.py

# NoA Personalized
ANTHROKIT_ANTHRO=none PERSONALITY_ADAPTATION=enabled streamlit run src/app_nonanthro_personalize.py
```

**LowA Conditions:**
```bash
# LowA Fixed
ANTHROKIT_ANTHRO=low PERSONALITY_ADAPTATION=disabled streamlit run src/app_condition_5.py

# LowA Personalized
ANTHROKIT_ANTHRO=low PERSONALITY_ADAPTATION=enabled streamlit run src/app_condition_5_personality.py
```

**HighA Conditions:**
```bash
# HighA Fixed
ANTHROKIT_ANTHRO=high PERSONALITY_ADAPTATION=disabled streamlit run src/app_v1.py

# HighA Personalized
ANTHROKIT_ANTHRO=high PERSONALITY_ADAPTATION=enabled streamlit run src/app_v1_personality.py
```

## Data Collection

**GitHub API Logging:**
- Session logs saved to private repository: `ksauka/hicxai-data-private`
- Directory structure: `interaction_logs/{NoA|LowA|HighA}/{session_id}.json`
- Requires `GITHUB_TOKEN` with 'repo' scope in `secrets.toml`

**Logged Data:**
- **Session metadata**: Prolific ID (mandatory), condition, timestamp
- **Tone configuration**: Base preset values + personality adjustments (if enabled)
- **Generation metadata**: Model name, temperature settings, boost flag
- **Interactions**: User inputs, assistant outputs, field validations
- **Task events**: Decision display, explanation triggers, feedback
- **Outcome measures**: Social presence, trust, satisfaction ratings

**Data Privacy:**
- No PII beyond Prolific ID
- Interaction logs stored in private GitHub repository
- Compliant with university research ethics guidelines

## Key Dependencies

- **AnthroKit**: Core framework (personality module, presets)
- **Streamlit**: Web application framework
- **OpenAI GPT-4o-mini**: Natural language generation (+0.25 temperature boost for HighA)
- **scikit-learn**: Loan classification model
- **GitHub API**: Interaction logging

## Acknowledgements

This implementation builds upon:
- **[XAgent](https://github.com/bach1292/XAgent)** by bach1292 - Original XAI agent framework
- **Adult Dataset** from [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/adult)
- **Question-Intent Dataset** curated by XAgent, adapted from Liao et al. (2020)

## Related Files

See parent [README.md](../README.md) for AnthroKit framework overview.
