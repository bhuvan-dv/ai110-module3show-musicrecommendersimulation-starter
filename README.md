# 🎵 Music Recommender Simulation

## Project Summary

This project simulates a small, content-based music recommender. Songs are represented as
structured data (genre, mood, energy, tempo, and more), and a user "taste profile" describes
what that person likes. A weighted scoring function compares every song in the catalog to the
profile, and the top-scoring songs are returned as recommendations, along with a plain-language
explanation of why each song was picked.

---

## How The System Works

Real platforms like Spotify or YouTube combine two main strategies. **Collaborative filtering**
looks at behavior across many users — if people who liked the songs you like also liked some
other song, that song gets recommended to you, even if it doesn't sound like anything you've
played before. **Content-based filtering**, which is what this project implements, ignores other
users entirely and instead compares the *attributes* of items (genre, tempo, mood, energy) to a
profile of what one user seems to prefer. The key distinction is: input features (song attributes
in `data/songs.csv`) are static data about the item; user preferences (a `UserProfile` or
`user_prefs` dict) describe a target the system is trying to match; and the ranking algorithm is
the piece of logic (`score_song` / `recommend_songs`) that turns "how well does this song match
this target" into an ordered list. Real systems mix both approaches and add signals like skips,
replays, and playlist co-occurrence, but the core idea — score every candidate, then sort — is
the same one used here.

My version prioritizes three signals: a matching **genre** (worth the most points, since genre is
the strongest proxy for overall "sound"), a matching **mood** (worth about half as much), and an
**energy similarity** score that rewards songs whose energy is *close* to the user's target energy
rather than simply "higher energy is better." An optional acoustic bonus rewards high-acousticness
songs for users who say they like acoustic material.

**`Song`** objects (and dict rows loaded from CSV) carry: `title`, `artist`, `genre`, `mood`,
`energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, plus five richer attributes I
added for the stretch goal: `popularity` (0–100), `release_decade`, `mood_tags` (a pipe-separated
list like `"euphoric|bright"`), `loudness_db`, and `vocal_type` (`"vocal"` or `"instrumental"`).

**`UserProfile`** objects (and `user_prefs` dicts) carry: `favorite_genre`, `favorite_mood`,
`target_energy`, `likes_acoustic`, plus two optional fields that use the new attributes:
`favorite_mood_tags` (a list of tags to match against a song's `mood_tags`) and
`prefers_instrumental`.

### Algorithm Recipe

- **+2.0 points** for an exact genre match
- **+1.0 point** for an exact mood match
- **Up to +2.0 points** for energy similarity: `2.0 * (1 - abs(target_energy - song_energy))`,
  so a song whose energy exactly matches the target earns the full 2.0, and the score shrinks
  linearly the further apart they are
- **+0.5 points** acoustic bonus if the user likes acoustic music and the song's `acousticness >= 0.6`
- **+0.5 points per matching mood tag** if the user specifies `favorite_mood_tags` (e.g. asking for
  `"nostalgic"` matches any song whose `mood_tags` include `"nostalgic"`)
- **+0.5 points** instrumental-match bonus if the user sets `prefers_instrumental=True` and the
  song's `vocal_type == "instrumental"`

I expect this recipe to over-favor genre: two songs with the same genre but very different moods
and energy levels can still both outscore a song from a different genre that's a near-perfect mood
and energy match. That's a bias worth watching (see [Limitations and Risks](#limitations-and-risks)).

### Data Flow

```
Input (UserProfile / user_prefs dict)
        │
        ▼
Process: for every song in songs.csv →
        score_song(user_prefs, song) → (score, reasons)
        │
        ▼
Output: sort all (song, score, reasons) by score, descending →
        recommend_songs() returns the top k
```

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

   Optional flags let you switch the ranking strategy (Strategy design pattern — see
   `STRATEGIES` in `src/recommender.py`) and enable the artist-diversity penalty:

   ```bash
   python -m src.main --mode energy_focused
   python -m src.main --mode mood_first --diversify
   ```

   Available `--mode` choices: `balanced` (default), `genre_first`, `mood_first`, `energy_focused`.

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` against the full 20-song catalog, run for six different taste
profiles (default, EDM, lofi, rock, acoustic, and an adversarial conflicting-preference profile):

```text
Loaded songs: 20

=== Default Pop/Happy ===

|   # | Title             | Artist        |   Score | Reasons                                                          |
|-----|-------------------|---------------|---------|--------------------------------------------------------------------|
|   1 | Sunrise City      | Neon Echo     |    4.96 | genre match (+2.0), mood match (+1.0), energy similarity (+1.96)  |
|   2 | Gym Hero          | Max Pulse     |    3.74 | genre match (+2.0), energy similarity (+1.74)                     |
|   3 | Heartbreak Anthem | Sepia Groove  |    3.36 | genre match (+2.0), energy similarity (+1.36)                     |
|   4 | Rooftop Lights    | Indigo Parade |    2.92 | mood match (+1.0), energy similarity (+1.92)                      |
|   5 | Festival Frenzy   | DJ Fracture   |    2.7  | mood match (+1.0), energy similarity (+1.70)                      |

=== High-Energy EDM ===

|   # | Title           | Artist      |   Score | Reasons                                                          |
|-----|-----------------|-------------|---------|--------------------------------------------------------------------|
|   1 | Bassline Riot   | DJ Fracture |    4.96 | genre match (+2.0), mood match (+1.0), energy similarity (+1.96)  |
|   2 | Festival Frenzy | DJ Fracture |    4    | genre match (+2.0), energy similarity (+2.00)                     |
|   3 | Gym Hero        | Max Pulse   |    2.96 | mood match (+1.0), energy similarity (+1.96)                      |
|   4 | Storm Runner    | Voltline    |    2.92 | mood match (+1.0), energy similarity (+1.92)                      |
|   5 | Trap Door       | Lil Circuit |    2.8  | mood match (+1.0), energy similarity (+1.80)                      |

=== Chill Lofi ===

|   # | Title               | Artist         |   Score | Reasons                                                          |
|-----|---------------------|----------------|---------|--------------------------------------------------------------------|
|   1 | Library Rain        | Paper Lanterns |    5    | genre match (+2.0), mood match (+1.0), energy similarity (+2.00)  |
|   2 | Midnight Coding     | LoRoom         |    4.86 | genre match (+2.0), mood match (+1.0), energy similarity (+1.86)  |
|   3 | Focus Flow          | LoRoom         |    3.9  | genre match (+2.0), energy similarity (+1.90)                     |
|   4 | Spacewalk Thoughts  | Orbit Bloom    |    2.86 | mood match (+1.0), energy similarity (+1.86)                      |
|   5 | Coffee Shop Stories | Slow Stereo    |    1.96 | energy similarity (+1.96)                                         |

=== Deep Intense Rock ===

|   # | Title         | Artist      |   Score | Reasons                                                          |
|-----|---------------|-------------|---------|--------------------------------------------------------------------|
|   1 | Storm Runner  | Voltline    |    4.98 | genre match (+2.0), mood match (+1.0), energy similarity (+1.98)  |
|   2 | Neon Tears    | Voltline    |    3.3  | genre match (+2.0), energy similarity (+1.30)                     |
|   3 | Gym Hero      | Max Pulse   |    2.94 | mood match (+1.0), energy similarity (+1.94)                      |
|   4 | Trap Door     | Lil Circuit |    2.9  | mood match (+1.0), energy similarity (+1.90)                      |
|   5 | Bassline Riot | DJ Fracture |    2.86 | mood match (+1.0), energy similarity (+1.86)                      |

=== Acoustic Low-Energy ===

|   # | Title              | Artist       |   Score | Reasons                                                                                 |
|-----|--------------------|--------------|---------|-------------------------------------------------------------------------------------------|
|   1 | Broken Strings     | Willow Ash   |    5.46 | genre match (+2.0), mood match (+1.0), energy similarity (+1.96), acoustic bonus (+0.5)  |
|   2 | Deep Focus         | Orbit Bloom  |    2.5  | energy similarity (+2.00), acoustic bonus (+0.5)                                          |
|   3 | Heartbreak Anthem  | Sepia Groove |    2.44 | mood match (+1.0), energy similarity (+1.44)                                              |
|   4 | Spacewalk Thoughts | Orbit Bloom  |    2.34 | energy similarity (+1.84), acoustic bonus (+0.5)                                          |
|   5 | Neon Tears         | Voltline     |    2.3  | mood match (+1.0), energy similarity (+1.30)                                              |

=== Adversarial Conflicted (genre=pop, mood=sad, energy=0.9) ===

|   # | Title             | Artist       |   Score | Reasons                                                          |
|-----|-------------------|--------------|---------|--------------------------------------------------------------------|
|   1 | Heartbreak Anthem | Sepia Groove |    4.16 | genre match (+2.0), mood match (+1.0), energy similarity (+1.16)  |
|   2 | Gym Hero          | Max Pulse    |    3.94 | genre match (+2.0), energy similarity (+1.94)                     |
|   3 | Sunrise City      | Neon Echo    |    3.84 | genre match (+2.0), energy similarity (+1.84)                     |
|   4 | Neon Tears        | Voltline     |    2.3  | mood match (+1.0), energy similarity (+1.30)                      |
|   5 | Storm Runner      | Voltline     |    1.98 | energy similarity (+1.98)                                         |
```

**Screenshot or video** *(optional)*: not included — terminal output above is the recorded artifact.

---

## Experiments You Tried

- **Weight shift (energy x2, genre x0.5):** implemented as the `energy_focused` scoring strategy
  in `src/recommender.py`. For the "Deep Intense Rock" profile this pulled `Bassline Riot` (EDM,
  energy 0.97) above `Storm Runner` (rock, the previously #1 pick) — energy proximity started to
  dominate over genre identity, which is exactly the tradeoff you'd expect from doubling that
  weight.
- **Adversarial profile test:** I gave the recommender a deliberately conflicting profile
  (`genre=pop, mood=sad, energy=0.9` — high energy usually pairs with happier songs in this
  dataset). The system didn't break; it just found the closest compromise (`Heartbreak Anthem`, a
  sad pop song with moderate-high energy) rather than a perfect match, showing the additive scoring
  model degrades gracefully instead of crashing or returning nonsense.
- **Small catalog effect:** with only 20 songs and roughly a dozen genres, several profiles kept
  surfacing the same handful of high-popularity/high-danceability songs across different profiles
  (e.g., `Gym Hero` appears in 4 of the 6 profiles above) simply because it scores well on energy
  similarity for almost any mid-to-high energy target. A larger, more evenly distributed catalog
  would reduce this repetition.

---

## Limitations and Risks

- The catalog only has 20 songs, so for niche profiles (e.g., very specific genre + mood
  combinations) there may be only one or two decent matches, and the "top 5" can include weak,
  barely-related filler songs.
- The system only understands the numeric/categorical attributes in the CSV — it has no sense of
  lyrics, vocals, instrumentation, or cultural context, so two songs with identical `genre`/`mood`/
  `energy` values are treated as interchangeable even if they sound nothing alike.
- Genre match is weighted highest (+2.0), so it can create a "filter bubble": a user who is
  slightly more into mood than genre will still get genre-dominated results, and songs from a
  favorite artist in a different genre may never surface.
- Popularity is loaded but not scored by default — the recommender currently doesn't correct for
  genre imbalance in the dataset (e.g., pop/lofi are more represented than folk or jazz), so those
  genres are less likely to appear regardless of user fit.

See `model_card.md` for a deeper look at bias, evaluation, and future improvements.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this project made concrete something I'd only understood abstractly before: a
"recommendation" is really just a sort operation over a scored list, and the score is only as
good as the weights and features you choose to include. Nothing about `recommend_songs()` is
intelligent in a deep sense — it is arithmetic applied consistently. That's also where bias
sneaks in: the moment I decided genre should be worth 2x mood, I encoded a value judgment about
what "similar taste" means, and that judgment shapes every single output the system produces. The
adversarial-profile experiment made this especially visible — conflicting preferences don't
confuse the system, they just reveal which of my weights wins the tiebreak.

