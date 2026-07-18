# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Expand `data/songs.csv` from 10 to 20 songs and add 5+ new meaningful attributes (popularity,
release_decade, mood_tags, loudness_db, vocal_type), then update `Song`, `UserProfile`,
`load_songs`, `score_song`, and the scoring strategies in `src/recommender.py` so the new fields
both load correctly *and* actually feed into the scoring logic — not just sit unused — without
breaking the existing `Song`/`UserProfile`/`Recommender` API expected by
`tests/test_recommender.py`.

**Prompts used:**

- "Generate 10 additional rows for songs.csv covering genres and moods not already present (edm,
  soul, acoustic, folk, hip-hop; sad and confident moods), matching the existing header exactly,
  plus new columns popularity (0-100 int), release_decade (e.g. '1990s'), mood_tags (a
  pipe-separated string like 'euphoric|bright'), loudness_db (a negative float like -6.0), and
  vocal_type ('vocal' or 'instrumental')."
- "Update the Song dataclass and load_songs() to include the new attributes with safe defaults so
  existing tests that construct Song() without those fields keep passing."
- "Add optional UserProfile fields (favorite_mood_tags, prefers_instrumental) and wire them into
  BalancedStrategy.score() and score_song() as small additive bonuses, so the new attributes
  actually influence the ranking instead of being loaded but ignored."

**What did the agent generate or change?**

- `data/songs.csv`: added 10 new rows and 5 new columns (`popularity`, `release_decade`,
  `mood_tags`, `loudness_db`, `vocal_type`) to all 20 rows.
- `src/recommender.py`: added the five new fields to the `Song` dataclass with defaults, added
  `favorite_mood_tags`/`prefers_instrumental` (both optional) to `UserProfile`, extended
  `load_songs()` to parse the new CSV columns, added a `_mood_tags_overlap_score()` helper, and
  wired a `+0.5`-per-matching-tag mood-tag bonus and a `+0.5` instrumental-match bonus into both
  `BalancedStrategy.score()` (OOP path) and `score_song()` (functional path).

**What did you verify or fix manually?**

I ran `pytest` after the change to confirm `Song(...)`/`UserProfile(...)` calls in
`tests/test_recommender.py` (which don't pass any of the new fields) still construct successfully
because of the defaults — both tests passed. I manually re-ran `python -m src.main` with the
original profiles to confirm scores were byte-for-byte unchanged (since none of those profiles set
`favorite_mood_tags`/`prefers_instrumental`, the new bonuses correctly stay at zero unless a user
opts in). I then manually tested a profile that *does* set `favorite_mood_tags` and
`prefers_instrumental` and confirmed the reasons list correctly reported "mood tag overlap" and
"instrumental match" bonuses only for songs that actually had overlapping tags / were
instrumental. I also spot-checked a few generated CSV rows (energy/tempo/loudness values) against
my own sense of the genre — e.g., making sure "ambient" tracks had low energy and very negative
loudness_db, and "edm" tracks had high energy and loud, near-zero loudness_db — since the agent
doesn't have real audio to check against.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

Strategy pattern, for switchable ranking modes.

**How did AI help you brainstorm or implement it?**

I asked how to let a user pick between multiple ranking strategies ("Genre-First," "Mood-First,"
"Energy-Focused") without duplicating the whole `recommend()` loop for each one. The suggestion
was the classic Strategy pattern: define a common `ScoringStrategy` interface with one `score()`
method, implement one subclass per strategy, and have `Recommender` hold a reference to whichever
strategy was selected at construction time. This kept the ranking/sorting logic in one place
(`Recommender.recommend`) while only the per-song scoring weights vary between modes.

**How does the pattern appear in your final code?**

`src/recommender.py` defines an abstract `ScoringStrategy` base class and four concrete strategies
(`BalancedStrategy`, `GenreFirstStrategy`, `MoodFirstStrategy`, `EnergyFocusedStrategy`), collected
in the `STRATEGIES` dict. `Recommender.__init__(self, songs, mode="balanced")` looks up the
matching strategy object and stores it as `self.strategy`; `recommend()` and
`explain_recommendation()` both just call `self.strategy.score(...)` without needing to know which
concrete strategy is active.
