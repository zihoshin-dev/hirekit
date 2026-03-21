<p align="center">
  <h1 align="center">HireKit</h1>
  <p align="center">
    <strong>AI-powered company analysis and interview preparation CLI for job seekers</strong>
  </p>
  <p align="center">
    Research companies. Match jobs. Ace interviews.
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/hirekit/"><img src="https://img.shields.io/pypi/v/hirekit" alt="PyPI"></a>
  <a href="https://github.com/ziho/hirekit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"></a>
</p>

---

## What is HireKit?

HireKit is an open-source CLI tool that automates company research for job seekers. It collects data from multiple sources (financial filings, news, GitHub, job postings), generates structured analysis reports, and helps you prepare for interviews — all from your terminal.

**The problem:** Researching a company before applying takes 4-8 hours of manual work across dozens of sources.

**The solution:** `hirekit analyze kakao` generates a comprehensive report in minutes.

## Features

- **Multi-source data collection** — DART filings, news, GitHub tech scoring, and more
- **Structured company reports** — 12-section analysis covering financials, culture, tech, competition
- **Weighted scorecard** — 5-dimension, 100-point company evaluation (not gut feeling)
- **LLM-optional** — Works without AI (template mode), enhanced with OpenAI/Anthropic/Ollama
- **Plugin architecture** — Add custom data sources with a simple Python interface
- **Privacy-first** — All data stays local, no external tracking

## Quick Start

```bash
# Install
pip install hirekit

# Configure (set up API keys)
hirekit configure

# Analyze a company
hirekit analyze 카카오

# View available data sources
hirekit sources
```

## Example Output

```
┌─────────────────────────────────────────┐
│          HireKit Analysis               │
│                                         │
│  Analyzing: 카카오                       │
│  Region: KR  Tier: 1  LLM: off         │
└─────────────────────────────────────────┘

┌──────────────── 카카오 Scorecard ────────────────┐
│ Dimension           Weight  Score  Evidence      │
│ Job Fit              30%    4.2/5  Strong PM...  │
│ Career Leverage      20%    3.8/5  Platform...   │
│ Growth Potential     20%    4.0/5  AI invest...  │
│ Compensation         15%    4.5/5  Top-tier...   │
│ Culture Fit          15%    3.5/5  Fast-paced... │
│ Total                       82/100  Grade S      │
└──────────────────────────────────────────────────┘

Report saved: ./reports/카카오_analysis.md
```

## Data Sources

| Source | Region | Data | API Key |
|--------|--------|------|---------|
| DART | KR | Financial filings, employee data | Required |
| Naver News | KR | Recent news articles | Required |
| GitHub | Global | Tech maturity scoring | gh CLI |
| *More coming...* | | | |

### Adding Custom Sources

```python
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

@SourceRegistry.register
class MySource(BaseSource):
    name = "my_source"
    region = "global"
    sections = ["tech"]

    def is_available(self) -> bool:
        return True

    def collect(self, company, **kwargs):
        # Your data collection logic here
        return [SourceResult(
            source_name=self.name,
            section="tech",
            data={"key": "value"},
        )]
```

## Configuration

Config lives in `~/.hirekit/config.toml`:

```toml
[analysis]
default_region = "kr"
cache_ttl_hours = 168  # 7 days

[llm]
provider = "none"  # openai, anthropic, ollama, none
model = "gpt-4o-mini"

[sources]
enabled = ["dart", "github", "naver_news"]

[output]
format = "markdown"
directory = "./reports"
```

## LLM Support

HireKit works without any LLM (template-based reports). For AI-enhanced analysis:

```bash
# OpenAI
pip install hirekit[openai]
# Set OPENAI_API_KEY in ~/.hirekit/.env

# Anthropic
pip install hirekit[anthropic]

# Local models via Ollama
pip install hirekit[ollama]

# Or use litellm for 100+ providers
pip install hirekit[llm]
```

## Roadmap

- [x] **Phase 1 (MVP):** DART + GitHub + News analysis, scorecard, Markdown reports
- [ ] **Phase 2:** JD matching (`hirekit match`), interview prep (`hirekit interview`), resume review
- [ ] **Phase 3:** US companies (SEC Edgar), web UI, community plugins

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Good first issues:**
- Add a new data source plugin
- Improve report templates
- Add i18n support

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with care for every job seeker out there.</sub>
</p>
