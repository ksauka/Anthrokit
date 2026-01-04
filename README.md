# AnthroKit: Personality-Adaptive Anthropomorphism Framework

**A research framework for personality-driven anthropomorphic AI interactions.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

**AnthroKit** is a research framework for operationalizing personality-adaptive anthropomorphism in conversational AI systems. The framework enables researchers to:

- Collect Big 5 personality traits via validated TIPI survey (Gosling et al., 2003)
- Map personality traits to anthropomorphic tone adjustments based on PERSONAGE (Mairesse & Walker, 2007)
- Apply adaptive optimization for user-specific anthropomorphism levels
- Track and analyze the relationship between personality, anthropomorphism, and user outcomes

## Research Context

**Paper:** "AnthroKit: A Framework for Personality-Adaptive Anthropomorphism"  
**Status:** Framework validation study in progress (N=20-30)  


### Core Research Question
Do personality traits moderate the relationship between anthropomorphism and social presence in AI interactions?

### Framework Components

**1. Personality Collection (TIPI/Big 5)**
- 10-item survey measuring Extraversion, Agreeableness, Conscientiousness, Neuroticism, Openness
- Session-cached responses with validation
- Reverse-coded scoring and trait averaging

**2. Trait-to-Token Mapping**
- Research-grounded mappings (e.g., Extraversion → warmth, Agreeableness → empathy)
- Equal weights (0.5/0.5) as theoretically neutral initial coefficients
- Personalization emerges from individual TIPI score differences
- Post-hoc optimization via regression on validation study data

**3. Anthropomorphism Presets**
- **HighA**: Warm, conversational tone with persona (warmth=0.70, empathy=0.55)
- **LowA**: Professional, neutral, system-focused (warmth=0.25, empathy=0.15)
- Personality adjustments: ±0.30 range based on centered trait scores

**4. Adaptive Optimization**
- Multi-armed bandit approach for real-time personalization
- Thompson Sampling with Beta priors
- Session tracking and outcome logging for post-hoc analysis

## Project Structure

```
AnthroKit/
├── anthrokit/              # Core Python package
│   ├── personality.py      # TIPI collection & trait-to-token mapping
│   ├── config.py           # Preset loading and management
│   ├── adaptive.py         # Thompson Sampling optimizer
│   ├── tracking.py         # Session and outcome logging
│   └── validators.py       # Safety guardrails
│
├── XAIagent/               # Example: XAI research study
│   ├── src/                # Loan assistant application
│   ├── data/               # Datasets
│   ├── models/             # ML models
│   ├── tests/              # Test suite
│   └── docs/               # Study documentation
│
├── setup.py                # Package installation
├── pyproject.toml          # Package metadata (PEP 517/518)
└── README.md               # This file
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/anthrokit.git
cd AnthroKit

# Install core package
pip install -e .

# Install with LLM stylization support
pip install -e ".[llm]"

# Install with API service
pip install -e ".[api]"

# Install everything
pip install -e ".[all]"
```

### Basic Usage: Scaffolds + Stylizer

```python
from anthrokit import load_preset, stylize_text
│
└── XAIagent/               # Validation study implementation
    ├── src/                # Streamlit applications
    │   ├── app_v1.py       # High anthropomorphism condition
    │   ├── app_condition_5.py  # Low anthropomorphism condition
    │   └── app_adaptive.py # Adaptive optimization demo
    ├── config/             # System prompts and presets
    └── data/               # Study datasets

```

## Installation

```bash
# Clone repository
git clone https://github.com/ksauka/Anthrokit.git
cd AnthroKit

# Install package
pip install -e .
```


### Key References

- **TIPI Scale**: Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003). A very brief measure of the Big-Five personality domains. *Journal of Research in Personality*, 37(6), 504-528.
- **PERSONAGE**: Mairesse, F., & Walker, M. (2007). PERSONAGE: Personality generation for dialogue. *ACL '07*.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

Kudzai Sauka - [GitHub](https://github.com/ksauka)

---

*This is a research framework under active development. Framework validation study in progress.*



## Citation

If you use AnthroKit in your research, please cite:

```bibtex
@software{anthrokit2026,
  title = {AnthroKit: Research-Grade Anthropomorphism Design System for Conversational AI},
  author = {AnthroKit Contributors},
  year = {2026},
  url = {https://github.com/your-org/anthrokit},
  note = {Domain-agnostic token-based framework for promoting social presence 
          in conversational AI through controlled anthropomorphism}
}
```

## Academic Grounding

AnthroKit is grounded in established HCI and psychology research:

- **HAX Guidelines** (Microsoft, CHI 2019 / TOCHI 2022) - Responsible AI interaction design
- **Three-Factor Anthropomorphism Theory** (Epley et al., 2007) - Psychological mechanisms
- **CASA Framework** (Nass & Moon, 2000) - Computers as social actors
- **Social Presence Theory** (Short et al., 1976) - Mediated communication
- **Recent Chatbot Research** (2022-2024) - Tone effects in conversational AI

### Key Publications
- Seering et al. (2019). "Designing User Interface Elements to Improve the Quality of Conversation"
- Candello et al. (2017). "Evaluating the conversation of conversational agents"
- Følstad & Brandtzæg (2020). "Chatbots: Changing user needs and motivations"
