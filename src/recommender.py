import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Song:
    """Represents a song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: float = 50.0
    release_decade: str = "2020s"
    mood_tags: str = ""
    loudness_db: float = -8.0
    vocal_type: str = "vocal"


@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    favorite_mood_tags: Optional[List[str]] = None
    prefers_instrumental: bool = False


GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 2.0
ACOUSTIC_BONUS = 0.5
ARTIST_PENALTY = 1.5
MOOD_TAG_WEIGHT = 0.5
VOCAL_TYPE_BONUS = 0.5


def _mood_tags_overlap_score(user_tags: Optional[List[str]], song_mood_tags: str, weight: float = MOOD_TAG_WEIGHT) -> float:
    """Awards points for each of the user's favorite mood tags found on the song."""
    if not user_tags or not song_mood_tags:
        return 0.0
    song_tags = {tag.strip().lower() for tag in song_mood_tags.split("|") if tag.strip()}
    matches = sum(1 for tag in user_tags if tag.strip().lower() in song_tags)
    return matches * weight


def _energy_similarity_score(target_energy: float, song_energy: float, weight: float = ENERGY_WEIGHT) -> float:
    """Rewards songs whose energy is close to the target (closer = higher score)."""
    gap = abs(target_energy - song_energy)
    return max(0.0, weight * (1 - gap))


class ScoringStrategy:
    """Base class for ranking strategies (Strategy design pattern)."""

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        raise NotImplementedError


class BalancedStrategy(ScoringStrategy):
    """Default recipe: genre +2.0, mood +1.0, energy similarity up to +2.0."""

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        total = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            total += GENRE_WEIGHT
            reasons.append(f"genre match (+{GENRE_WEIGHT:.1f})")

        if song.mood == user.favorite_mood:
            total += MOOD_WEIGHT
            reasons.append(f"mood match (+{MOOD_WEIGHT:.1f})")

        energy_points = _energy_similarity_score(user.target_energy, song.energy)
        if energy_points > 0:
            total += energy_points
            reasons.append(f"energy similarity (+{energy_points:.2f})")

        if user.likes_acoustic and song.acousticness >= 0.6:
            total += ACOUSTIC_BONUS
            reasons.append(f"acoustic bonus (+{ACOUSTIC_BONUS:.1f})")

        mood_tag_points = _mood_tags_overlap_score(user.favorite_mood_tags, song.mood_tags)
        if mood_tag_points > 0:
            total += mood_tag_points
            reasons.append(f"mood tag overlap (+{mood_tag_points:.1f})")

        if user.prefers_instrumental and song.vocal_type == "instrumental":
            total += VOCAL_TYPE_BONUS
            reasons.append(f"instrumental match (+{VOCAL_TYPE_BONUS:.1f})")

        return total, reasons


class GenreFirstStrategy(ScoringStrategy):
    """Weights genre matches heavily; mood and energy matter less."""

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        total = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            total += GENRE_WEIGHT * 2
            reasons.append(f"genre match (+{GENRE_WEIGHT * 2:.1f})")

        if song.mood == user.favorite_mood:
            total += MOOD_WEIGHT * 0.5
            reasons.append(f"mood match (+{MOOD_WEIGHT * 0.5:.1f})")

        energy_points = _energy_similarity_score(user.target_energy, song.energy, weight=1.0)
        if energy_points > 0:
            total += energy_points
            reasons.append(f"energy similarity (+{energy_points:.2f})")

        return total, reasons


class MoodFirstStrategy(ScoringStrategy):
    """Weights mood matches heavily; genre and energy matter less."""

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        total = 0.0
        reasons: List[str] = []

        if song.mood == user.favorite_mood:
            total += MOOD_WEIGHT * 3
            reasons.append(f"mood match (+{MOOD_WEIGHT * 3:.1f})")

        if song.genre == user.favorite_genre:
            total += GENRE_WEIGHT * 0.5
            reasons.append(f"genre match (+{GENRE_WEIGHT * 0.5:.1f})")

        energy_points = _energy_similarity_score(user.target_energy, song.energy, weight=1.0)
        if energy_points > 0:
            total += energy_points
            reasons.append(f"energy similarity (+{energy_points:.2f})")

        return total, reasons


class EnergyFocusedStrategy(ScoringStrategy):
    """Doubles the importance of energy similarity, halves genre weight."""

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        total = 0.0
        reasons: List[str] = []

        energy_points = _energy_similarity_score(user.target_energy, song.energy, weight=ENERGY_WEIGHT * 2)
        if energy_points > 0:
            total += energy_points
            reasons.append(f"energy similarity (+{energy_points:.2f})")

        if song.genre == user.favorite_genre:
            total += GENRE_WEIGHT * 0.5
            reasons.append(f"genre match (+{GENRE_WEIGHT * 0.5:.1f})")

        if song.mood == user.favorite_mood:
            total += MOOD_WEIGHT
            reasons.append(f"mood match (+{MOOD_WEIGHT:.1f})")

        return total, reasons


STRATEGIES: Dict[str, ScoringStrategy] = {
    "balanced": BalancedStrategy(),
    "genre_first": GenreFirstStrategy(),
    "mood_first": MoodFirstStrategy(),
    "energy_focused": EnergyFocusedStrategy(),
}


class Recommender:
    """OOP implementation of the recommendation logic."""

    def __init__(self, songs: List[Song], mode: str = "balanced"):
        self.songs = songs
        self.strategy = STRATEGIES.get(mode, STRATEGIES["balanced"])

    def recommend(self, user: UserProfile, k: int = 5, diversify: bool = False) -> List[Song]:
        """Ranks all songs against the user profile and returns the top k."""
        scored = [(song, self.strategy.score(user, song)[0]) for song in self.songs]

        if not diversify:
            ranked = sorted(scored, key=lambda pair: pair[1], reverse=True)
            return [song for song, _ in ranked[:k]]

        # Diversity penalty: subtract points each time an artist already appears in the picks.
        remaining = sorted(scored, key=lambda pair: pair[1], reverse=True)
        picks: List[Song] = []
        artist_counts: Dict[str, int] = {}
        while remaining and len(picks) < k:
            adjusted = [
                (song, score - ARTIST_PENALTY * artist_counts.get(song.artist, 0))
                for song, score in remaining
            ]
            adjusted.sort(key=lambda pair: pair[1], reverse=True)
            best_song, _ = adjusted[0]
            picks.append(best_song)
            artist_counts[best_song.artist] = artist_counts.get(best_song.artist, 0) + 1
            remaining = [(song, score) for song, score in remaining if song.id != best_song.id]
        return picks

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a human-readable reason for why a song was recommended."""
        _, reasons = self.strategy.score(user, song)
        if not reasons:
            return "No strong preference matches; included as a filler recommendation."
        return ", ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file into a list of dicts with numeric fields converted."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
                "popularity": float(row.get("popularity", 50.0)),
                "release_decade": row.get("release_decade", ""),
                "mood_tags": row.get("mood_tags", ""),
                "loudness_db": float(row.get("loudness_db", -8.0)),
                "vocal_type": row.get("vocal_type", "vocal"),
            })
    return songs


_MODE_WEIGHTS = {
    "balanced": {"genre": GENRE_WEIGHT, "mood": MOOD_WEIGHT, "energy": ENERGY_WEIGHT},
    "genre_first": {"genre": GENRE_WEIGHT * 2, "mood": MOOD_WEIGHT * 0.5, "energy": 1.0},
    "mood_first": {"genre": GENRE_WEIGHT * 0.5, "mood": MOOD_WEIGHT * 3, "energy": 1.0},
    "energy_focused": {"genre": GENRE_WEIGHT * 0.5, "mood": MOOD_WEIGHT, "energy": ENERGY_WEIGHT * 2},
}


def score_song(user_prefs: Dict, song: Dict, mode: str = "balanced") -> Tuple[float, List[str]]:
    """Scores a single song dict against a user_prefs dict using the Algorithm Recipe."""
    weights = _MODE_WEIGHTS.get(mode, _MODE_WEIGHTS["balanced"])
    total = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs.get("genre"):
        total += weights["genre"]
        reasons.append(f"genre match (+{weights['genre']:.1f})")

    if song["mood"] == user_prefs.get("mood"):
        total += weights["mood"]
        reasons.append(f"mood match (+{weights['mood']:.1f})")

    target_energy = user_prefs.get("energy")
    if target_energy is not None:
        energy_points = _energy_similarity_score(target_energy, song["energy"], weight=weights["energy"])
        if energy_points > 0:
            total += energy_points
            reasons.append(f"energy similarity (+{energy_points:.2f})")

    if user_prefs.get("likes_acoustic") and song.get("acousticness", 0) >= 0.6:
        total += ACOUSTIC_BONUS
        reasons.append(f"acoustic bonus (+{ACOUSTIC_BONUS:.1f})")

    mood_tag_points = _mood_tags_overlap_score(user_prefs.get("favorite_mood_tags"), song.get("mood_tags", ""))
    if mood_tag_points > 0:
        total += mood_tag_points
        reasons.append(f"mood tag overlap (+{mood_tag_points:.1f})")

    if user_prefs.get("prefers_instrumental") and song.get("vocal_type") == "instrumental":
        total += VOCAL_TYPE_BONUS
        reasons.append(f"instrumental match (+{VOCAL_TYPE_BONUS:.1f})")

    return total, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: str = "balanced", diversify: bool = False) -> List[Tuple[Dict, float, str]]:
    """Scores every song, ranks them, and returns the top k as (song, score, explanation) tuples."""
    scored = [(song, *score_song(user_prefs, song, mode=mode)) for song in songs]

    if not diversify:
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    else:
        remaining = scored
        ordered: List[Tuple[Dict, float, List[str]]] = []
        artist_counts: Dict[str, int] = {}
        while remaining:
            adjusted = [
                (song, score - ARTIST_PENALTY * artist_counts.get(song["artist"], 0), reasons)
                for song, score, reasons in remaining
            ]
            adjusted.sort(key=lambda item: item[1], reverse=True)
            best_song, _, best_reasons = adjusted[0]
            original_score = next(score for song, score, _ in remaining if song["id"] == best_song["id"])
            ordered.append((best_song, original_score, best_reasons))
            artist_counts[best_song["artist"]] = artist_counts.get(best_song["artist"], 0) + 1
            remaining = [item for item in remaining if item[0]["id"] != best_song["id"]]
        ranked = ordered

    top = ranked[:k]
    explanations = []
    for song, score, reasons in top:
        explanation = ", ".join(reasons) if reasons else "no strong preference matches"
        explanations.append((song, score, explanation))
    return explanations
