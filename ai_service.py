import os
import json
import random
from typing import Dict, Any, List, Optional
from python_backend.risk_engine import calculate_injury_risk

MEDICAL_DISCLAIMER = "\n\n*Disclaimer: This is educational fitness guidance only, not a medical diagnosis. If you experience severe, shooting, or persistent pain, numbness, swelling, or loss of mobility, please stop exercising immediately and seek a professional medical diagnosis.*"

def generate_fallback_analysis(
    profile: Optional[Dict[str, Any]],
    recent_workouts: List[Dict[str, Any]],
    recent_pain_reports: List[Dict[str, Any]]
) -> Dict[str, Any]:
    risk = calculate_injury_risk(recent_workouts, recent_pain_reports, profile)
    
    body_part = recent_pain_reports[0]["BodyPart"] if recent_pain_reports else "General"
    exercise = recent_pain_reports[0]["Exercise"] if recent_pain_reports else "workout"

    causes = []
    recommendations = []
    recovery_advice = []
    safer_alternatives = []

    body_part_lower = body_part.lower()
    if "shoulder" in body_part_lower:
        causes = [
            f"Excessive elbow flaring during {exercise or 'bench presses'} placing high shear force on the anterior deltoids.",
            "Minor rotator cuff impingement due to pushing volume mismatch compared to back pulling/scapular retraction.",
            "Inadequate dynamic warm-up targeting shoulder rotators and serratus anterior."
        ]
        recommendations = [
            "Angle your elbows at 45 degrees relative to your torso on pushing exercises rather than wide 90 degrees.",
            "Implement a 2:1 ratio of back pulling (pullups, rows, facepulls) to chest pressing volume.",
            "Focus on stretching chest/anterior deltoids and strengthening rotator cuff muscles (internal/external rotations)."
        ]
        recovery_advice = [
            "Apply ice if throbbing or hot; use heat to increase blood flow if stiff.",
            "Take 5-7 days off heavy vertical or horizontal pressing movements.",
            "Perform daily band pull-aparts and sleeper stretches for mobility."
        ]
        safer_alternatives = [
            "Dumbbell Floor Press (restricts excessive shoulder hyperextension)",
            "Incline Dumbbell Press (reduces pressure on front deltoid)",
            "Chest-Supported Dumbbell Rows (targets back stabilizers)"
        ]
    elif "knee" in body_part_lower:
        causes = [
            "Patellar tendon tracking issues caused by tight quadriceps or weak gluteus medius pulling knee inward.",
            f"Sudden increase in deep bending volume or weight on {exercise or 'squats'} without proper ankle mobility.",
            "Poor knee alignment (knees caving in / valgus collapse) during loaded lower body exercises."
        ]
        recommendations = [
            "Squeeze your glutes and push knees outward dynamically while squatting.",
            "Perform foam rolling and static stretches on tight quadriceps and IT-bands.",
            "Limit depth to parallel instead of deep 'ass-to-grass' until knee joints stabilize."
        ]
        recovery_advice = [
            "Rest from high-impact running or heavy bilateral squatting for 7-10 days.",
            "Ice knee for 15 minutes after workouts if minor swelling occurs.",
            "Incorporate low-impact swimming or steady stationary cycling to maintain joint lubrication."
        ]
        safer_alternatives = [
            "Goblet Squats (forces upright torso and better glute activation)",
            "Leg Press (limits spinal loading and stabilizes knee track)",
            "Box Squats (prevents bottom-range knee stress)"
        ]
    elif "back" in body_part_lower or "spine" in body_part_lower:
        causes = [
            f"Lumbar spine rounding under load during {exercise or 'deadlifts or squats'} due to fatigue or core collapse.",
            "Poor hip hinge mechanics shifting the load onto the spinal erectors instead of hamstrings and glutes.",
            "Weak deep abdominal core muscles (transverse abdominis) failing to stabilize the lumbar curve."
        ]
        recommendations = [
            "Maintain a rigid, neutral flat back at all times when pulling or squatting.",
            "Incorporate bracing protocols (Valsalva maneuver) prior to every repetition.",
            "Decrease working load by 20-30% and master the hip hinge with bodyweight or wooden dowels."
        ]
        recovery_advice = [
            "Perform 'Cat-Cow' stretches and gentle abdominal hollowing daily.",
            "Avoid long-duration sitting which compresses spinal discs further.",
            "Use gentle walking to encourage active blood flow to lower back muscles."
        ]
        safer_alternatives = [
            "Trap Bar Deadlift (keeps load centered closer to gravity)",
            "Chest-Supported Dumbbell Rows (completely deloads lumbar spine)",
            "Plank variations (trains core stabilization without flexion)"
        ]
    else:
        # General / Catch-all Fallback
        causes = [
            "Sudden increase in workout frequency or intensity exceeding muscular recovery capacity.",
            "Muscle imbalance surrounding the affected joints, leading to compensation.",
            "Insufficient joint warm-up or missing mobility/stretching work."
        ]
        recommendations = [
            "Reduce weight by 20-40% on exercises that stimulate pain and focus on eccentric control.",
            "Double down on daily sleep quality, hydration, and protein intake to aid tissue recovery.",
            "Track training volume strictly to prevent sudden overreaching."
        ]
        recovery_advice = [
            "Apply active recovery protocols: light stretching and zone 2 cardio.",
            "Adopt a minimum of 2 complete rest days per week.",
            "Incorporate dynamic stretching routines before your lifting session."
        ]
        safer_alternatives = [
            "Bodyweight exercises targeting the muscle groups",
            "Cable machine alternatives (controls mechanical tension path)",
            "Isolations that bypass the painful joint"
        ]

    contributing = ", ".join(f["factor"] for f in risk["factors"])
    risk_explanation = f"Risk scored at {risk['score']}/30 (Category: {risk['level']}). Key warning flags include: {contributing}."

    return {
        "causes": causes,
        "recommendations": recommendations,
        "recoveryAdvice": recovery_advice,
        "saferAlternatives": safer_alternatives,
        "riskLevel": risk["level"],
        "riskExplanation": risk_explanation,
        # Direct frontend compatibility mapping fields
        "riskScore": risk["score"],
        "factors": causes,
        "rehabTips": recovery_advice,
        "explanation": risk_explanation
    }

async def generate_analysis(
    profile: Optional[Dict[str, Any]],
    recent_workouts: List[Dict[str, Any]],
    recent_pain_reports: List[Dict[str, Any]]
) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "MY_GEMINI_API_KEY":
        return generate_fallback_analysis(profile, recent_workouts, recent_pain_reports)

    risk = calculate_injury_risk(recent_workouts, recent_pain_reports, profile)
    
    # Format inputs for prompt
    if recent_pain_reports:
        latest = recent_pain_reports[0]
        pain_context = (
            f"Latest Pain Report:\n"
            f"- Affected Body Part: {latest.get('BodyPart')}\n"
            f"- Pain Level: {latest.get('PainLevel')}/10\n"
            f"- Pain Type: {latest.get('PainType')}\n"
            f"- Duration: {latest.get('Duration')}\n"
            f"- Trigger Exercise: {latest.get('Exercise')}\n"
            f"- User Notes: {latest.get('Notes') or 'None'}"
        )
    else:
        pain_context = "No recent pain reports logged."

    if profile:
        profile_context = (
            f"User Fitness Profile:\n"
            f"- Age: {profile.get('Age')}, Gender: {profile.get('Gender')}\n"
            f"- Height: {profile.get('Height')} cm, Weight: {profile.get('Weight')} kg, BMI: {profile.get('BMI')}\n"
            f"- Lifting Experience: {profile.get('Experience')}\n"
            f"- Goal: {profile.get('Goal')}"
        )
    else:
        profile_context = "No fitness profile completed yet."

    if recent_workouts:
        workout_context = "Recent Workouts Logged (Last 10 days):\n" + "\n".join(
            f"- Date: {w.get('WorkoutDate')}, Exercise: {w.get('Exercise')}, Muscle: {w.get('MuscleGroup')}, "
            f"Sets: {w.get('Sets')}, Reps: {w.get('Reps')}, Weight: {w.get('Weight')}kg, Difficulty: {w.get('Difficulty')}"
            for w in recent_workouts[:8]
        )
    else:
        workout_context = "No workouts logged in the system yet."

    prompt = (
        f"You are an expert Sports Medicine & Athletic Injury Prevention assistant.\n"
        f"Analyze this athlete's data to estimate injury risk, describe possible causes, and suggest safer exercises and recovery advice.\n\n"
        f"{profile_context}\n\n"
        f"{pain_context}\n\n"
        f"{workout_context}\n\n"
        f"Our rule-based risk algorithm calculated a preliminary score of {risk['score']}/30 with risk category \"{risk['level']}\".\n"
        f"Take this calculation into account but do a comprehensive biomechanical, athletic evaluation.\n\n"
        f"You MUST respond strictly with a valid JSON object matching this schema:\n"
        f"{{\n"
        f'  "causes": ["cause 1", "cause 2"],\n'
        f'  "recommendations": ["rec 1", "rec 2"],\n'
        f'  "recoveryAdvice": ["advice 1", "advice 2"],\n'
        f'  "saferAlternatives": ["alt 1", "alt 2"],\n'
        f'  "riskLevel": "Low" | "Medium" | "High",\n'
        f'  "riskExplanation": "detailed explanation"\n'
        f"}}\n\n"
        f"Ensure all statements are educational, non-medical, and reference specific exercises or body parts mentioned in the context."
    )

    try:
        # Try importing new google-genai SDK first
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            # Standard structural type config
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            text = response.text
        except Exception as e:
            print(f"Primary google-genai library call failed/missing, trying google-generativeai: {e}")
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text

        if text:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "", 1).replace("```", "", 1).strip()
            parsed = json.loads(cleaned)
            
            # Normalize risk level
            rl = str(parsed.get("riskLevel", "")).lower()
            if "high" in rl:
                parsed["riskLevel"] = "High"
            elif "med" in rl:
                parsed["riskLevel"] = "Medium"
            else:
                parsed["riskLevel"] = "Low"

            # Fill in UI mapping fields
            parsed["riskScore"] = risk["score"]
            parsed["factors"] = parsed.get("causes", [])
            parsed["rehabTips"] = parsed.get("recoveryAdvice", [])
            parsed["explanation"] = parsed.get("riskExplanation", "")
            return parsed

        raise Exception("Empty text returned from Gemini API")

    except Exception as err:
        print(f"Error generating analysis from Gemini, using fallback: {err}")
        return generate_fallback_analysis(profile, recent_workouts, recent_pain_reports)


async def chat_reply(
    profile: Optional[Dict[str, Any]],
    recent_workouts: List[Dict[str, Any]],
    recent_pain_reports: List[Dict[str, Any]],
    question: str
) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Helper local reply generator
    def get_local_reply():
        q_lower = question.lower()
        if "shoulder" in q_lower or "bench" in q_lower or "chest" in q_lower:
            reply = (
                "**Shoulder Safety:** Shoulder pinching during bench press is often rotator cuff impingement.\n"
                "• **Tip:** Pin your shoulder blades back/down; angle elbows at 45° (don't flare to 90°).\n"
                "• **Alternative:** Try **Dumbbell Floor Press** to restrict deep shoulder hyperextension, and perform band facepulls."
            )
        elif "squat" in q_lower or "knee" in q_lower or "leg" in q_lower:
            reply = (
                "**Knee Protection:** Knee strain in squats usually stems from knees caving inward or tight quads.\n"
                "• **Tip:** Push knees outward dynamically during the lift, and foam roll your quadriceps.\n"
                "• **Alternative:** Swap back squats for **Goblet Squats** (keeps torso upright) or stable **Leg Press** (higher foot placement)."
            )
        elif "back" in q_lower or "deadlift" in q_lower or "row" in q_lower:
            reply = (
                "**Lower Back Care:** Back stiffness often results from lumbar rounding or poor hip hinges.\n"
                "• **Tip:** Keep a flat spine, brace your core, and keep the bar close to your shins.\n"
                "• **Alternative:** Switch to **Chest-Supported Rows** or **Trap Bar Deadlifts** to deload spinal forces."
            )
        elif any(k in q_lower for k in ["diet", "food", "eat", "protein", "nutrition", "meal", "calorie"]):
            reply = (
                "**Recovery Nutrition & Diet:**\n"
                "• **Protein:** Target 1.6 to 2.2 grams per kg of bodyweight daily to repair exercise-induced micro-tears in muscle tissues.\n"
                "• **Anti-Inflammatory Nutrition:** Integrate Omega-3 rich foods (salmon, walnuts, chia seeds) and antioxidants to minimize joint swelling and support cartilage.\n"
                "• **Hydration & Glycogen:** Maintain high water intake to keep synovial fluid lubricated, and replenish energy with clean complex carbohydrates (oatmeal, sweet potatoes)."
            )
        else:
            pain_part = recent_pain_reports[0]["BodyPart"] if recent_pain_reports else None
            pain_level = recent_pain_reports[0]["PainLevel"] if recent_pain_reports else None
            status_str = f"• **Active Pain:** {pain_part} (Level {pain_level}/10). Rest recommended." if pain_part else "• **Status:** No active pain. Great job!"
            hist_str = f"• **History:** {len(recent_workouts)} logged workouts. Avoid training spikes." if recent_workouts else "• **History:** No workouts logged yet."
            
            reply = (
                f"Hi! I'm your AI Coach. Based on your profile:\n"
                f"{status_str}\n"
                f"{hist_str}\n\n"
                f"**Injury Prevention Essentials:**\n"
                f"1. Limit weekly volume increases to <10%.\n"
                f"2. Maintain 1-2 full rest days weekly.\n"
                f"3. Replace painful moves with safe alternatives immediately.\n\n"
                f"What specific joints, exercises, or recovery nutrition should we optimize?"
            )
        return reply

    if not api_key or api_key == "MY_GEMINI_API_KEY":
        return get_local_reply() + MEDICAL_DISCLAIMER

    # Prepare Context strings
    if recent_pain_reports:
        latest = recent_pain_reports[0]
        pain_context = f"User reports pain in their {latest.get('BodyPart')} (Level {latest.get('PainLevel')}/10, Type: {latest.get('PainType')}) from {latest.get('Exercise')}."
    else:
        pain_context = "User has no active pain reports logged."

    if profile:
        profile_context = f"User profile: Age {profile.get('Age')}, experience level is {profile.get('Experience')}, goal is {profile.get('Goal')}."
    else:
        profile_context = "User profile is not completed."

    workout_names = ", ".join(w.get("Exercise", "") for w in recent_workouts[:3])
    recent_workout_summary = f"Recent workouts list: {workout_names}." if workout_names else "No recent workouts logged."

    prompt = (
        f"You are a professional, safety-first AI Coach specializing in workout biomechanics, injury prevention, and recovery.\n"
        f'The user is asking a health, exercise, recovery, or nutrition question: "{question}"\n\n'
        f"Provide a concise, direct, and relevant answer strictly under 150 words. Focus on:\n"
        f"1. Directly addressing their query with practical, actionable tips (e.g. food options if asking about diet, technique cues if asking about lifts).\n"
        f"2. Tying it back briefly to training safety, recovery, joint health, or biomechanics where logical.\n"
        f"3. Using brief bullet points and bold headers to keep it extremely readable and easy to scan.\n\n"
        f"**User Profile & Context:**\n"
        f"- {profile_context}\n"
        f"- {pain_context}\n"
        f"- {recent_workout_summary}\n\n"
        f"Provide your answer below (strictly under 150 words):"
    )

    system_instruction = (
        "You are an expert, friendly AI Workout Coach specializing in biomechanics, injury prevention, joint health, and athletic nutrition. "
        "Provide clear, direct, and relevant guidance tailored exactly to what the user asks. Always keep your responses highly concise, "
        "direct, and under 150 words using clean markdown bullet points. Do not write essays or verbose paragraphs. Get straight to the point."
    )

    try:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            reply = response.text
        except Exception as e:
            print(f"Primary google-genai library call failed/missing for chat, trying google-generativeai: {e}")
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            reply = response.text

        if reply:
            return reply.strip() + MEDICAL_DISCLAIMER
        raise Exception("Empty chat response")

    except Exception as err:
        print(f"All Gemini model calls failed, using local biomechanical fallback: {err}")
        note = "*(Note: Upstream AI is currently experiencing high load; displaying local biomechanical guidelines)*\n\n"
        return note + get_local_reply() + MEDICAL_DISCLAIMER
