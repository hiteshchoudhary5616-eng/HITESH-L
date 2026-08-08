import datetime
from typing import List, Dict, Any, Optional

def calculate_injury_risk(
    workouts: List[Dict[str, Any]],
    pain_reports: List[Dict[str, Any]],
    profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    score = 0.0
    factors = []
    now = datetime.datetime.now()

    # Helper to parse dates safely
    def parse_date(date_str: str) -> datetime.datetime:
        # Expected formats: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...
        if "T" in date_str:
            date_part = date_str.split("T")[0]
        else:
            date_part = date_str
        return datetime.datetime.strptime(date_part, "%Y-%m-%d")

    # 1. Pain Level Contribution
    if pain_reports:
        # Assumed sorted by date desc
        latest_pain = pain_reports[0]
        try:
            pain_date = parse_date(latest_pain["ReportDate"])
            days_since_pain = (now - pain_date).days
            
            # Only count pain reports from the last 7 days as active indicators
            if days_since_pain <= 7:
                pain_score = latest_pain["PainLevel"] * 1.5
                score += pain_score
                factors.append({
                    "factor": f"Active {latest_pain['BodyPart']} Pain (Level {latest_pain['PainLevel']}/10)",
                    "scoreContribution": round(pain_score, 1)
                })

                # Sharp or burning pain represents higher tissue/nerve warning
                pain_type_lower = latest_pain["PainType"].lower()
                if "sharp" in pain_type_lower or "burn" in pain_type_lower:
                    score += 3.0
                    factors.append({
                        "factor": f"High-Risk Pain Type ({latest_pain['PainType']})",
                        "scoreContribution": 3.0
                    })
        except Exception as e:
            print(f"Error parsing pain report date: {e}")

    # 2. Workout Frequency (Sessions in last 7 days)
    one_week_ago = now - datetime.timedelta(days=7)
    recent_workouts = []
    for w in workouts:
        try:
            w_date = parse_date(w["WorkoutDate"])
            if w_date >= one_week_ago:
                recent_workouts.append((w, w_date))
        except Exception as e:
            print(f"Error parsing workout date: {e}")

    frequency = len(recent_workouts)
    if frequency > 5:
        score += 5.0
        factors.append({
            "factor": f"Overtraining Frequency ({frequency} workouts/week)",
            "scoreContribution": 5.0
        })
    elif frequency >= 4:
        score += 2.0
        factors.append({
            "factor": f"High Training Frequency ({frequency} workouts/week)",
            "scoreContribution": 2.0
        })

    # 3. Sudden Training Volume Spike (Last 3 days vs Previous 4 days of the week)
    three_days_ago = now - datetime.timedelta(days=3)
    last_3_days_workouts = [w for w, w_date in recent_workouts if w_date >= three_days_ago]
    prev_4_days_workouts = [w for w, w_date in recent_workouts if w_date < three_days_ago]

    vol_last_3 = sum(float(w["Weight"]) * int(w["Sets"]) * int(w["Reps"]) for w in last_3_days_workouts)
    vol_prev_4 = sum(float(w["Weight"]) * int(w["Sets"]) * int(w["Reps"]) for w in prev_4_days_workouts)

    avg_vol_last_3 = vol_last_3 / 3.0
    avg_vol_prev_4 = vol_prev_4 / 4.0

    if avg_vol_prev_4 > 0 and (avg_vol_last_3 / avg_vol_prev_4) > 1.3:
        spike_percent = round(((avg_vol_last_3 / avg_vol_prev_4) - 1) * 100)
        score += 4.0
        factors.append({
            "factor": f"Sudden Volume Spike (+{spike_percent}% in last 3 days)",
            "scoreContribution": 4.0
        })

    # 4. Consecutive Workout Days (Lack of Rest)
    consecutive_days = 0
    workout_dates = set()
    for w in workouts:
        try:
            # Standardize date to YYYY-MM-DD
            d_str = w["WorkoutDate"].split("T")[0]
            workout_dates.add(d_str)
        except:
            pass

    sorted_unique_dates = sorted(list(workout_dates), reverse=True)
    if sorted_unique_dates:
        check_date = datetime.date.today()
        for _ in range(7):
            date_str = check_date.isoformat()
            if date_str in sorted_unique_dates:
                consecutive_days += 1
                check_date -= datetime.timedelta(days=1)
            else:
                break

    if consecutive_days >= 5:
        score += 5.0
        factors.append({
            "factor": f"Insufficient Rest ({consecutive_days} consecutive training days)",
            "scoreContribution": 5.0
        })
    elif consecutive_days >= 3:
        score += 2.0
        factors.append({
            "factor": f"Moderate Fatigue ({consecutive_days} consecutive training days)",
            "scoreContribution": 2.0
        })

    # 5. Workout Intensity vs Experience Level Mismatch
    if profile:
        level = profile.get("Experience", "Beginner")
        hard_workouts = [w for w, _ in recent_workouts if w.get("Difficulty") in ["Hard", "Very Hard"]]
        
        if level == "Beginner" and len(hard_workouts) >= 2:
            score += 4.0
            factors.append({
                "factor": "Beginner performing high-difficulty movements",
                "scoreContribution": 4.0
            })
        elif level == "Intermediate" and any(w.get("Difficulty") == "Very Hard" for w, _ in recent_workouts):
            score += 2.0
            factors.append({
                "factor": "Intermediate training at extreme difficulty",
                "scoreContribution": 2.0
            })

    # Calculate final category
    risk_level = "Low"
    if score >= 15:
        risk_level = "High"
    elif score >= 7:
        risk_level = "Medium"

    # Cap score to 30 for visual metrics
    display_score = min(round(score), 30)

    # Fallback factor if none triggered
    if not factors:
        factors = [{"factor": "Balanced Training Volume & Adequate Recovery", "scoreContribution": 0.0}]

    return {
        "score": display_score,
        "level": risk_level,
        "factors": factors
    }
