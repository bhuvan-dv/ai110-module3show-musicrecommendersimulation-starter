# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Intended Use

VibeMatch generates a ranked list of songs from a fixed catalog that best match a single user's
stated taste profile (favorite genre, favorite mood, target energy, and whether they like acoustic
songs). It assumes the user's preferences can be captured well by three or four simple attributes
— it does not learn from listening history, skips, or likes over time, and it does not compare
users to each other. This is a classroom exploration/teaching tool, not a production system: it is
meant to make the mechanics of a content-based recommender visible and explainable, not to power a
real streaming app.

---

## 3. How the Model Works

For every song in the catalog, VibeMatch checks three things: does the song's genre match the
user's favorite genre, does the song's mood match the user's favorite mood, and how close is the
song's energy level to the energy the user asked for. A genre match is worth the most points, a
mood match is worth about half that, and energy gets "similarity" points — the closer the song's
energy is to what the user wants, the more points it earns, even if it's not a perfect match.
Songs that are acoustic get a small bonus if the user says they like acoustic music. Every song
ends up with a total score and a list of plain-English reasons ("genre match", "energy
similarity"), and the songs are then sorted from highest to lowest score — the top handful become
the recommendations. Compared to the starter logic (which just returned the first k songs
unranked), the real change is that every song is now actually judged and compared before anything
is recommended.

---

## 4. Data

The catalog has 20 songs (expanded from the original 10) spanning genres like pop, lofi, rock,
ambient, jazz, synthwave, edm, soul, acoustic, folk, and hip-hop, and moods including happy, chill,
intense, relaxed, moody, focused, and sad. Each song has 15 attributes: genre, mood, energy,
tempo_bpm, valence, danceability, acousticness, and five attributes I added — popularity (0–100),
release_decade, mood_tags (e.g., "euphoric|bright"), loudness_db, and vocal_type
("vocal"/"instrumental"). Even at 20 songs, pop and lofi are
somewhat overrepresented relative to genres like folk or soul, which each only appear once — real
platforms have millions of tracks and much more even genre coverage, so this dataset can't capture
niche or emerging musical styles.

---

## 5. Strengths

The system works best for users with a clear, single dominant preference — e.g., "High-Energy
EDM" or "Chill Lofi" — where genre, mood, and energy all point in the same direction. In those
cases the top result is almost always a song I'd intuitively pick myself (e.g., "Bassline Riot"
for the EDM profile, "Library Rain" for the chill lofi profile). The energy-similarity scoring
(rather than "higher is always better") correctly distinguishes a *low*-energy target from a
*high*-energy one, so a "chill" profile doesn't accidentally surface intense songs just because
they have a high raw energy number.

---

## 6. Limitations and Bias

The scoring logic weights genre matches (+2.0) higher than mood matches (+1.0), which means the
system can over-prioritize genre even when a user's mood preference is the stronger signal — a
user who wants "sad" songs above all else will still see genre-matching happy songs ranked
similarly high. Because pop and lofi are the most common genres in the dataset, songs like "Gym
Hero" and "Sunrise City" keep reappearing across very different profiles simply because they score
well on energy similarity for a wide range of targets — this is a small-scale version of a
"filter bubble," where popular, energy-flexible songs crowd out great, more niche matches. The
system also has no notion of fairness across artists by default: nothing stops the same artist
from appearing multiple times in one user's top 5, which would make results feel repetitive over
time. I addressed this with an opt-in diversity component (see below), but it is not the default
behavior.

### Diversity / Fairness Component

`Recommender.recommend(..., diversify=True)` and `recommend_songs(..., diversify=True)` implement
an artist-repetition penalty: after the initial ranking, the recommender builds the top-k list one
slot at a time, and each time it picks a song it subtracts `1.5` points per prior appearance of
that song's artist from every remaining candidate's score before picking the next slot. This
directly targets "filter bubble" repetition — without it, an artist with several catalog entries
that all score well for a given profile (e.g., DJ Fracture appearing twice for the "High-Energy
EDM" profile) can crowd out other artists from the recommendation list even though those other
artists may represent a similar quality match. For example, for the EDM profile above, the
non-diversified top 5 places DJ Fracture's "Bassline Riot" **and** "Festival Frenzy" at #1 and #2;
with `diversify=True`, "Festival Frenzy" drops to #5 (its raw score of 4.0 is penalized because
DJ Fracture already appears once in the list), letting Max Pulse, Voltline, and Lil Circuit's
songs surface sooner. This trades a small amount of pure score-accuracy for more varied artist
representation in the final list — a basic move toward fairness across artists rather than just
raw score.

---

## 7. Evaluation

I tested six profiles: Default Pop/Happy, High-Energy EDM, Chill Lofi, Deep Intense Rock, Acoustic
Low-Energy (which also enables the acoustic bonus), and an adversarial "Conflicted" profile
(genre=pop, mood=sad, energy=0.9 — a combination that doesn't naturally occur together in the
dataset). All outputs are pasted as code blocks in the README's Sample Recommendation Output
section. What surprised me: the adversarial profile didn't break anything or return nonsense — it
just picked the best available compromise ("Heartbreak Anthem," a sad pop song with fairly high
energy), which shows the additive scoring degrades gracefully rather than failing outright.
Comparing profiles pairwise: the EDM profile prefers high-energy, danceable tracks ("Bassline
Riot," "Festival Frenzy"), while the Chill Lofi profile shifts entirely toward low-energy,
high-acousticness tracks ("Library Rain," "Midnight Coding") — makes sense, since those two
profiles have opposite target_energy values and different genres. The Acoustic Low-Energy profile
and the Chill Lofi profile overlap somewhat (both favor low energy), but the acoustic bonus pulls
in "Broken Strings" and "Deep Focus," which the lofi profile ranks lower because they aren't lofi
genre — showing that a secondary bonus (acoustic) can outweigh a missing genre match. I also ran
the "energy x2 / genre x0.5" weight-shift experiment (implemented as the `energy_focused`
strategy in `recommender.py`): under that weighting, "Bassline Riot" (EDM) outranked "Storm Runner"
(rock) for the Deep Intense Rock profile purely because its energy was closer to the target,
confirming that raising the energy weight really does trade off genre fidelity for energy
precision, as expected mathematically.

To a non-programmer: "Gym Hero" keeps showing up for "Happy Pop" listeners because the song is
high-energy and moderately upbeat — the system doesn't actually "know" it's a gym song, it just
sees that its numbers (energy, mood match) line up with what a lot of different happy/energetic
profiles are asking for. It's a coincidence of the math, not a deliberate judgment about the song.

---

## 8. Future Work

- Add a diversity/fairness pass by default (the artist-penalty logic already exists in
  `Recommender.recommend(diversify=True)` and `recommend_songs(diversify=True)`, but isn't the
  default) so repeat artists don't dominate every top-5 list.
- Incorporate `popularity` into the default scoring — right now it's loaded and available but not
  scored by default, even though `mood_tags` and `vocal_type` are now used via the optional
  `favorite_mood_tags`/`prefers_instrumental` preferences.
- Expand the catalog well beyond 20 songs and rebalance genre representation, so niche profiles
  don't run out of good matches and popular songs stop dominating every list by default.

---

## 9. Personal Reflection

My biggest learning moment was realizing how much of a "recommendation" is really just an
opinionated sort — the algorithm has no taste of its own, it just faithfully replays whatever
weights I chose. Using an AI coding assistant helped me quickly scaffold the CSV loading and
sorting logic and stress-test it against adversarial profiles, but I had to manually double-check
that the energy-similarity formula actually rewarded *closeness* rather than just "higher energy,"
since an early version I considered would have gotten that backwards. It surprised me how
convincing a simple additive score can feel — even without any real learning happening, the
top results for the EDM and lofi profiles matched my own intuition closely, which says a lot about
how far basic content-based matching alone can get in practice, and also how easy it would be to
mistake "the math worked out" for "the system understands music." If I extended this project, I'd
want to try blending in a lightweight collaborative signal (e.g., "users who liked X also liked
Y") on top of the content-based score, to see how much that shifts results away from
attribute-only matching.
