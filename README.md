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
  <a href="https://github.com/zihoshin-dev/hirekit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"></a>
  <a href="https://github.com/zihoshin-dev/hirekit"><img src="https://img.shields.io/github/stars/zihoshin-dev/hirekit?style=social" alt="Stars"></a>
</p>

---

## Why It Matters

You're in an interview. Your interviewer asks: **"Why do you want to work here?"**

You pause. You didn't research the company beyond the job posting.

**90% of rejected candidates cite "unprepared" as feedback.**

Meanwhile, company research takes **4-8 hours** across fragmented sources:
- DART filings (Korean finance jargon, hard to parse)
- News articles (biased, scattered across 10+ sites)
- Glassdoor reviews (complaint-focused, outdated)
- GitHub (tech only, no culture insights)
- LinkedIn, internal wikis, salary data

No tool combines these into one actionable intelligence report.

**HireKit solves this:** One command, 2 minutes, 8 data sources, 1 decision-ready report.

---

## How It Works

```bash
# Step 1: Install (30 seconds)
$ pip install hirekit

# Step 2: Configure API keys (1 minute, one-time)
$ hirekit configure
> DART API Key: [paste]
> Naver Client ID: [paste]

# Step 3: Analyze a company (2 minutes)
$ hirekit analyze 카카오

# Output: 12-section decision report
```

**Total time: 3 minutes vs. 4-8 hours of manual research**

---

## What You Get

**Single Actionable Score: 0-100 Job Fit Rating**

```
82/100 = Strong Opportunity (Go for it)
75/100 = Competitive (Worth applying with prep)
60/100 = Caution (Red flags exist — investigate)
```

**12-Section Report covering:**
- Executive summary with key reasons
- Financial health (salary negotiation potential)
- Tech stack & interview depth questions
- Recent news & company trajectory
- Culture & team dynamics
- Risk flags & mitigation strategies
- Interview prep tips specific to this company

**Multi-source cross-validation:**
- 8+ data sources collected in parallel
- Conflicts highlighted ("News says growing, DART shows debt spike — investigate")
- Evidence-based scoring, not gut feeling
- All sources cited with dates

---

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

---

## What's Next?

After analyzing a company, you can:

```bash
# Compare companies side-by-side
$ hirekit compare 카카오 네이버 --focus salary,growth

# Match your resume to a job posting
$ hirekit match https://wanted.co.kr/job-123 resume.pdf

# Prepare interview questions specific to this company
$ hirekit interview 카카오 --role backend-engineer

# Get interview feedback on your resume
$ hirekit resume review resume.pdf --company 카카오
```

👉 **[Full Tutorial](docs/tutorial.md)** | **[CLI Reference](docs/cli-reference.md)** | **[FAQ](docs/faq.md)**

---

## Features

- **8-source parallel collection** — DART financials, Google/Naver/Brave/Exa news, Reuters, Korean biz press, GitHub tech scoring, Glassdoor reviews (all collected simultaneously)
- **12-section structured reports** — Executive summary, financial health, tech stack, news/trajectory, culture, compensation, growth potential, risks, interview prep, scorecard, similar companies, action items
- **Weighted 5-dimension scorecard** — Job Fit (30%), Career Leverage (20%), Growth Potential (20%), Compensation (15%), Culture Fit (15%) — 100-point decision score, not subjective rating
- **LLM-optional** — Works without any AI (template mode for offline use), enhanced with OpenAI/Anthropic/Ollama for deeper analysis
- **Plugin architecture** — Add custom data sources in 20 lines of Python, no core changes needed
- **Privacy-first** — All data stays local, no external tracking, no cloud uploads

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

## Demo

```
$ hirekit analyze 카카오 --no-llm -o terminal

╭──────────────────── HireKit Analysis ────────────────────╮
│ Analyzing: 카카오                                        │
│ Region: kr  Tier: 1  LLM: off                            │
╰──────────────────────────────────────────────────────────╯

                     카카오 Scorecard
┌─────────────────────┬────────┬────────┬──────────────────┐
│ Dimension           │ Weight │  Score │ Evidence         │
├─────────────────────┼────────┼────────┼──────────────────┤
│ Job Fit             │    30% │  3.5/5 │ Tech stack data  │
│ Career Leverage     │    20% │  4.6/5 │ 15 data points   │
│ Growth Potential    │    20% │  4.5/5 │ Financials +     │
│                     │        │        │ active news      │
│ Compensation        │    15% │  3.5/5 │ DART salary data │
│ Culture Fit         │    15% │  4.5/5 │ Reviews + Exa    │
│ Total               │        │ 82/100 │ Grade S          │
└─────────────────────┴────────┴────────┴──────────────────┘
```

> 8 data sources collected 15 results in parallel — DART financials, Google/Naver/Brave/Exa news, Reuters, Korean biz press, GitHub tech scoring, Glassdoor reviews.

## Data Sources

| Source | Region | Data | API Key |
|--------|--------|------|---------|
| DART | KR | Financial filings, employee data | `DART_API_KEY` |
| Naver News | KR | Recent news articles | `NAVER_CLIENT_ID` |
| Naver Search | KR | Blog, cafe, web (culture/interview) | `NAVER_CLIENT_ID` |
| GitHub | Global | Tech maturity scoring | gh CLI |
| Google News | Global | RSS news (no key needed) | - |
| Credible News | Global | Reuters, Bloomberg, FT, WSJ + Korean biz press | - |
| Brave Search | Global | Web + news semantic search | `BRAVE_API_KEY` |
| Exa Search | Global | AI semantic deep search | `EXA_API_KEY` |

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

- [x] **Phase 1:** DART + GitHub + News analysis, scorecard, Markdown reports
- [x] **Phase 2:** JD matching (`hirekit match`), interview prep (`hirekit interview`), resume review (`hirekit resume`)
- [ ] **Phase 3:** US companies (SEC Edgar), web UI, community plugins, PyPI publish

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
