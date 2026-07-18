"""
Command line runner for the Music Recommender Simulation.

Loads the song catalog, scores it against several user "taste profiles",
and prints a ranked, explained list of recommendations for each. Pass
--mode to switch ranking strategies and --diversify to enable the
artist-repetition penalty.
"""

import argparse

try:
    from recommender import load_songs, recommend_songs, STRATEGIES
except ImportError:
    from src.recommender import load_songs, recommend_songs, STRATEGIES

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


PROFILES = {
    "Default Pop/Happy": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "High-Energy EDM": {"genre": "edm", "mood": "intense", "energy": 0.95},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.9},
    "Acoustic Low-Energy": {"genre": "acoustic", "mood": "sad", "energy": 0.2, "likes_acoustic": True},
    # Adversarial: conflicting preferences (high energy target + sad mood)
    "Adversarial Conflicted": {"genre": "pop", "mood": "sad", "energy": 0.9},
}


def print_recommendations(title: str, recommendations) -> None:
    print(f"\n=== {title} ===\n")
    if HAS_TABULATE:
        rows = [
            (rank, song["title"], song["artist"], f"{score:.2f}", explanation)
            for rank, (song, score, explanation) in enumerate(recommendations, start=1)
        ]
        print(tabulate(rows, headers=["#", "Title", "Artist", "Score", "Reasons"], tablefmt="github"))
    else:
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"{rank}. {song['title']} by {song['artist']} — Score: {score:.2f}")
            print(f"   Because: {explanation}")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation CLI")
    parser.add_argument(
        "--mode",
        choices=sorted(STRATEGIES.keys()),
        default="balanced",
        help="Ranking strategy to apply on top of the base score_song recipe (default: balanced).",
    )
    parser.add_argument(
        "--diversify",
        action="store_true",
        help="Apply the artist-repetition penalty so the same artist appears less often in the top k.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Ranking mode: {args.mode} | diversify: {args.diversify}\n")

    for title, user_prefs in PROFILES.items():
        recommendations = recommend_songs(user_prefs, songs, k=5, mode=args.mode, diversify=args.diversify)
        print_recommendations(title, recommendations)


if __name__ == "__main__":
    main()
