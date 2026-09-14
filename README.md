# Marketing Research Digest

Automated pipeline that pulls new articles from a curated list of marketing,
advertising and consumer-research journals, uses Claude to write a pitchable
digest for two audiences, fact-checks its own output against the abstracts, and
publishes every run to a browsable dashboard.

Built on [senior-research-digest](https://github.com/Meggers1982/senior-research-digest):
same shape, same scoring idea, same dashboard (the freelance-opps design system
by way of AgingWire). What differs is below in **Where this differs**.

## How it works

`.github/workflows/daily-digest.yml` runs `scripts/main.py` once a day. The cron
asks for 07:37 UTC; GitHub queues scheduled runs, so expect it hours late
(2.5 to 4.5 hours is typical across these repos, 11.5 the worst seen). Each run:

1. **Picks today's topic** from the rotation in `config/digest_config.json`
   (a broad day plus 13 topics, by day of year), or the `focus` input of a
   manual run.
2. **Searches OpenAlex** (`openalex.py`) for everything the 177 indexed journals
   published in the last 60 days, narrowed on topic days by a boolean
   title-and-abstract query from `topics.py`.
3. **Screens** (`screening.py`) down to 40 articles: drops front matter, articles
   with no abstract, off-topic articles in the adjacent journals, and anything an
   earlier digest already wrote up; ranks the rest by journal rating, recency and
   topic relevance, at most three per journal. Every drop is counted.
4. **Writes the digest** (`digest_generator.py`): Claude picks the newsworthy
   studies and returns one record each — headline, the study, why it matters, an
   angle for marketers, an angle for general readers, caveats. Journal, date and
   DOI are stamped on from OpenAlex, not written by the model.
5. **Fact-checks itself** (`fact_checker.py`): a second pass compares every entry
   with its abstract and returns a verdict and issues per study.
6. **Checks whether the press already has it** (`web_coverage.py`, Google News via
   SerpAPI). Skipped, and labelled as skipped, without `SERPAPI_API_KEY`.
7. **Synthesizes** (`trends.py`): continuity with the last run on the same topic,
   a cross-study feature pitch with outlets, and a story idea per study, plus a
   per-topic memory file in `topic_memory/`.
8. **Writes the run** to `outputs/` — the digest and fact check as markdown for
   people, and a `.json` run record — then rebuilds `docs/data/`.
9. **Commits and pushes.** The push is the deploy: Vercel's Git integration
   builds every commit on `main`, and `vercel.json` serves `docs/`.

`python -m pytest tests/ -q` runs first in the same workflow. It touches no API.

## Where this differs from senior-research-digest

- **OpenAlex, not PubMed.** PubMed indexes almost none of these journals.
  OpenAlex has them all but 12 (the practitioner outlets: Think with Google,
  Nielsen, Kantar, Admap, MSI working papers, and a few small titles). Measured
  2026-09-14: 1,089 works in 30 days from 138 journals, 75% with an abstract.
  **Elsevier titles are the gap** — Elsevier does not share abstracts with
  OpenAlex, so Journal of Business Research, Journal of Retailing and Consumer
  Services and IJRM carry one for about a third of their articles. Those are
  dropped and counted, and the dashboard's limits panel says how many.
- **Journals are keyed by OpenAlex source ID**, resolved once by
  `scripts/resolve_sources.py` and stored in `config/journals.csv`. Fourteen rows
  on the list have "unverified" in place of an ISSN and two had theirs mangled by
  a spreadsheet; a source ID survives both.
- **The dashboard reads records, not markdown.** senior-research-digest parses
  the model's markdown back with regexes (the format drift there once hid half
  the archive's verdicts). Here the run record in `outputs/*.json` holds exactly
  what the model returned; the markdown is rendered from it and nothing parses it.
- **A study is written up once.** Screening drops any work ID or DOI a previous
  run covered, read from the run records — new-scientist-story-ideas' ledger,
  without a second file to keep in sync.
- **Scoring is marketing's evidence ladder.** Field experiments, meta-analyses
  and large behavioral datasets score highest; multi-study experiments next;
  surveys analyzed with structural models, qualitative work and reviews lowest,
  because they measure stated attitudes. Journal tier comes from the list's own
  FT50 / ABDC 2025 / AJG 2021 ratings (unrated is neutral, not low).
  The band thresholds are senior-research-digest's and have **not** been tuned
  against this archive yet.
- **One run a day**, not two. No topic-demand report and no feed into
  research-digest-dashboard.

## Setup

Secrets (Settings → Secrets and variables → Actions):

| Secret | Needed | What happens without it |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | the run stops before OpenAlex |
| `SERPAPI_API_KEY` | no | coverage is not checked; no study can band as "Lead" |
| `OPENALEX_API_KEY` | no | anonymous limit of 1,000 calls a day; a run uses about 15 |

Run it by hand: Actions → Daily Marketing Research Digest → Run workflow, with
an optional topic.

## Changing things

- **Topics:** `config/digest_config.json` for the rotation; `scripts/topics.py`
  for each topic's OpenAlex query and tag terms. A rotation topic must exist in
  both — a test checks it.
- **Journals:** edit `config/journals.csv` (it is a copy of
  `~/Documents/Marketing Research Journals/Marketing Research Journals.csv` plus
  two OpenAlex columns), then run `python scripts/resolve_sources.py`. A near-miss
  name is recorded as "no match; closest: …" rather than accepted, because two
  titles on the list carry hijacked-title warnings.
- **Hide a bad run:** add its id to `docs/data/hidden.json` (`{"ids": [...]}`) and
  rebuild with `python scripts/build_dashboard_data.py`. Nothing is deleted.
- **Re-score the archive:** `python scripts/build_dashboard_data.py`. No API calls.

On this Mac, use `python3.11` (the repo needs 3.10+; the python.org 3.11 has no CA
bundle, so live OpenAlex calls need
`SSL_CERT_FILE=$(python3.11 -c "import certifi; print(certifi.where())")`).
