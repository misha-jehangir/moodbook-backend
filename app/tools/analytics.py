# Mapping string moods to numeric values for calculation
MOOD_MAP = {
    "Terrible": 1,
    "Bad": 2,
    "Neutral": 3,
    "Good": 4,
    "Excellent": 5
}

REV_MOOD_MAP = {v: k for k, v in MOOD_MAP.items()}

def calculate_mood_average(entries: list) -> float:
    """
    Calculates the average numeric mood score for a list of entries.
    """
    if not entries:
        return 0.0
    scores = [MOOD_MAP.get(e.get("mood"), 3) for e in entries]
    return sum(scores) / len(scores)

def compare_periods(current_entries: list, past_entries: list) -> dict:
    """
    Compares two lists of entries (e.g., current month vs last month)
    and returns average scores, differences, and progression status.
    """
    avg_curr = calculate_mood_average(current_entries)
    avg_past = calculate_mood_average(past_entries)
    diff = avg_curr - avg_past
    
    return {
        "current_average": round(avg_curr, 2),
        "past_average": round(avg_past, 2),
        "difference": round(diff, 2),
        "status": "improved" if diff > 0.1 else ("declined" if diff < -0.1 else "stable")
    }

def calculate_correlations(entries: list, min_frequency: int = 3) -> dict:
    """
    Analyzes which activities (reasons) and emotions correlate with higher or lower mood.
    Calculates the average mood when a tag is present versus the overall mood average.
    """
    if not entries:
        return {
            "overall_average": 0.0,
            "total_entries_analyzed": 0,
            "activity_correlations": [],
            "emotion_correlations": []
        }

    overall_avg = calculate_mood_average(entries)
    
    activity_stats = {}
    emotion_stats = {}

    for entry in entries:
        mood_val = MOOD_MAP.get(entry.get("mood"), 3)
        
        # Aggregate mood scores by activity (reasons)
        for activity in entry.get("reasons", []):
            if activity not in activity_stats:
                activity_stats[activity] = []
            activity_stats[activity].append(mood_val)
            
        # Aggregate mood scores by emotion
        for emotion in entry.get("emotions", []):
            if emotion not in emotion_stats:
                emotion_stats[emotion] = []
            emotion_stats[emotion].append(mood_val)

    # Helper function to compile and sort the aggregates
    def compile_stats(stats_dict):
        results = []
        for tag, scores in stats_dict.items():
            freq = len(scores)
            if freq >= min_frequency:
                avg_mood = sum(scores) / freq
                diff = avg_mood - overall_avg
                results.append({
                    "name": tag,
                    "frequency": freq,
                    "average_mood": round(avg_mood, 2),
                    "difference_from_average": round(diff, 2)
                })
        
        # Sort from highest positive impact (largest difference) to lowest/negative impact
        results.sort(key=lambda x: x["difference_from_average"], reverse=True)
        return results

    return {
        "overall_average": round(overall_avg, 2),
        "total_entries_analyzed": len(entries),
        "activity_correlations": compile_stats(activity_stats),
        "emotion_correlations": compile_stats(emotion_stats)
    }
