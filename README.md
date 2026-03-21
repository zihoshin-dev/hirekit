<p align="center">
  <h1 align="center">HireKit</h1>
  <p align="center">
    <strong>AI-powered company research & interview prep CLI for job seekers</strong>
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

<p align="center">
  <a href="README.ko.md">한국어</a> | English
</p>

---

## The Problem

You found a great job posting. Now you need to research the company before applying.

So you open 10+ tabs: DART filings, news sites, Glassdoor, GitHub, LinkedIn, salary databases...

**4-8 hours later**, you have scattered notes and still aren't sure if this company is right for you.

## The Solution

```bash
pip install hirekit
hirekit analyze 카카오
```

**2 minutes later**: A structured report with a 0-100 score, covering financials, culture, tech stack, recent news, and interview tips — all from 8 data sources collected in parallel.

---

## Quick Start

### 1. Install

```bash
pip install hirekit
```

> Requires Python 3.11+. That's it — no other setup needed for basic use.

### 2. Get API Keys (optional but recommended)

HireKit works with **zero API keys** (Google News + credible news sources are free). For richer data, get these free keys:

| Key | Where to get it | What it unlocks |
|-----|----------------|-----------------|
| DART API Key | [opendart.fss.or.kr](https://opendart.fss.or.kr/) | Korean company financials, salary, headcount |
| Naver Client ID/Secret | [developers.naver.com](https://developers.naver.com/) | Korean news, blog reviews, interview tips |
| Brave API Key | [brave.com/search/api](https://brave.com/search/api/) | Web + news semantic search |
| Exa API Key | [exa.ai](https://exa.ai/) | AI-powered deep search |

### 3. Configure

```bash
hirekit configure
```

This creates `~/.hirekit/config.toml` and `~/.hirekit/.env`. Open the `.env` file and paste your API keys:

```bash
# ~/.hirekit/.env
DART_API_KEY=your_key_here
NAVER_CLIENT_ID=your_id_here
NAVER_CLIENT_SECRET=your_secret_here
```

### 4. Analyze a Company

```bash
hirekit analyze 카카오
```

You'll see a scorecard like this:

```
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

A Markdown report is saved to `./reports/카카오_analysis.md`.

---

## All Commands

HireKit has 7 commands covering the full job preparation journey:

### `hirekit analyze` — Research a company

```bash
# Basic analysis (saves Markdown report)
hirekit analyze 카카오

# Show results in terminal instead of saving
hirekit analyze 네이버 -o terminal

# JSON output (for scripting)
hirekit analyze 토스 -o json

# Quick analysis (fewer sections)
hirekit analyze 쿠팡 --tier 3
```

### `hirekit match` — Match a job posting to your profile

```bash
# Paste a JD URL
hirekit match "https://www.wanted.co.kr/wd/12345"

# Or use a saved JD text file
hirekit match jd.txt

# With your career profile for personalized matching
hirekit match jd.txt --profile ~/.hirekit/profile.yaml
```

**What you get**: Match score (0-100), skill gaps, strengths, and application strategy.

### `hirekit interview` — Prepare for interviews

```bash
# Generate interview questions for a company
hirekit interview 카카오

# Specify your target position
hirekit interview 카카오 --position "Backend Engineer"

# Show in terminal
hirekit interview 네이버 --position PM -o terminal
```

**What you get**: 5 common questions, role-specific questions, STAR story templates, and 5 reverse questions to ask the interviewer.

### `hirekit coverletter` — Draft a Korean cover letter (자기소개서)

```bash
# Generate a 4-section Korean cover letter draft
hirekit coverletter 카카오 --position PM

# With your profile for personalized content
hirekit coverletter 토스 --position PM --profile profile.yaml

# Preview in terminal
hirekit coverletter 네이버 -o terminal
```

**What you get**: 4-section draft (성장과정, 지원동기, 직무역량, 장단점) with per-section scoring and improvement feedback.

### `hirekit resume` — Review your resume

```bash
# Review a resume file
hirekit resume resume.md

# Review against a specific job description
hirekit resume resume.md --jd "https://wanted.co.kr/wd/12345"

# With career profile
hirekit resume resume.pdf --profile profile.yaml
```

**What you get**: ATS compatibility check, structure analysis, keyword gaps vs JD, content quality score, and improvement suggestions.

### `hirekit sources` — Check data source status

```bash
hirekit sources
```

Shows which data sources are configured and ready:

```
                    Data Sources
┌────────────┬────────┬─────────────────┬────────────────┐
│ Name       │ Region │ API Key         │ Status         │
├────────────┼────────┼─────────────────┼────────────────┤
│ dart       │ KR     │ DART_API_KEY    │ Ready          │
│ github     │ GLOBAL │ -               │ Ready          │
│ google_news│ GLOBAL │ -               │ Ready          │
│ naver_news │ KR     │ NAVER_CLIENT_ID │ Not configured │
└────────────┴────────┴─────────────────┴────────────────┘
```

### `hirekit configure` — Set up API keys and preferences

```bash
hirekit configure
```

Creates default config files. Edit `~/.hirekit/.env` to add your API keys.

---

## Data Sources (8 built-in)

| Source | Region | What it provides | API Key | Free? |
|--------|--------|-----------------|---------|-------|
| **DART** | Korea | Financials, salary, headcount from official filings | `DART_API_KEY` | Yes |
| **Naver News** | Korea | Recent Korean news articles | `NAVER_CLIENT_ID` | Yes |
| **Naver Search** | Korea | Blog/cafe reviews, interview tips, culture info | `NAVER_CLIENT_ID` | Yes |
| **GitHub** | Global | Tech maturity score (repos, stars, languages) | gh CLI auth | Yes |
| **Google News** | Global | Latest news via RSS | None needed | Yes |
| **Credible News** | Global | Reuters, Bloomberg, FT, WSJ + Korean biz press | None needed | Yes |
| **Brave Search** | Global | Web + news semantic search | `BRAVE_API_KEY` | Free tier |
| **Exa Search** | Global | AI-powered semantic deep search | `EXA_API_KEY` | Free tier |

> You can start with **zero API keys**. Google News, Credible News, and GitHub (if you have `gh` CLI) work without any setup.

---

## AI Enhancement (Optional)

HireKit works perfectly without AI — reports are generated using templates and rules. To get deeper, AI-powered analysis:

```bash
# Install with OpenAI support
pip install "hirekit[openai]"

# Or Anthropic Claude
pip install "hirekit[anthropic]"

# Or local models via Ollama (fully offline, free)
pip install "hirekit[ollama]"
```

Then set your API key in `~/.hirekit/.env`:

```bash
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

And update `~/.hirekit/config.toml`:

```toml
[llm]
provider = "openai"  # or "anthropic", "ollama"
model = "gpt-4o-mini"
```

---

## Career Profile (Optional)

Create `~/.hirekit/profile.yaml` to get personalized matching:

```yaml
name: "Your Name"
years_of_experience: 5

tracks:
  - name: "Product Manager"
    priority: 1

career_assets:
  - asset: "Built payment system"
    source: "Previous Company"
    applicable_industries: ["fintech", "ecommerce"]

skills:
  technical: ["Python", "SQL", "Data Analysis"]
  domain: ["Payment Systems", "E-commerce"]
  soft: ["Cross-functional Communication"]

preferences:
  regions: ["kr"]
  industries: ["fintech", "platform"]
  work_style: ["hybrid"]
```

When you pass `--profile`, HireKit matches your skills against job requirements and tailors interview questions to your experience.

---

## Adding Custom Data Sources

Want to add your own data source? It's just one Python class:

```python
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

@SourceRegistry.register
class GlassdoorSource(BaseSource):
    name = "glassdoor"
    region = "global"
    sections = ["culture"]

    def is_available(self) -> bool:
        return True  # or check for API key

    def collect(self, company, **kwargs):
        # Your scraping/API logic here
        return [SourceResult(
            source_name=self.name,
            section="culture",
            data={"rating": 4.2, "reviews": 150},
            raw="Glassdoor rating: 4.2/5 from 150 reviews",
        )]
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Roadmap

- [x] **v0.1** — Company analysis, scorecard, 8 data sources
- [x] **v0.1** — JD matching, interview prep, resume review, cover letter coach
- [ ] **v0.2** — US companies (SEC Edgar), improved report quality
- [ ] **v0.3** — Web UI, community plugins, agent architecture

---

## Contributing

We welcome contributions! Here are some good starting points:

- Add a new data source (Glassdoor, LinkedIn, SEC Edgar)
- Improve Korean cover letter templates
- Add support for Japanese/Chinese job markets
- Improve the scoring algorithm

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

---

## License

MIT License. See [LICENSE](LICENSE).

<p align="center">
  <sub>Built for every job seeker who deserves better tools.</sub>
</p>
