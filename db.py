import os
import json
import bcrypt
import datetime
from typing import List, Dict, Any, Optional

# File path settings: check workspace root, then fall back to local folder
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db_storage.json"))
if not os.path.exists(DB_FILE):
    DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "db_storage.json"))

# Global In-Memory representation synced to file
db: Dict[str, List[Dict[str, Any]]] = {
    "Users": [],
    "FitnessProfile": [],
    "Exercises": [],
    "WorkoutHistory": [],
    "PainReports": [],
    "AIRecommendations": [],
    "RecoveryPlans": [],
    "ChatHistory": [],
    "Notifications": [],
    "PasswordReset": [],
    "ActivityLog": []
}

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Error saving DB_FILE: {e}")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_db():
    global db
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Merge loaded data with defaults to ensure all keys exist
            for key in db.keys():
                db[key] = loaded.get(key, [])
            
            # Ensure seed users have valid password hashes in the existing JSON database
            modified = False
            admin_user = next((u for u in db["Users"] if u["Email"].lower() == "admin@demo.com"), None)
            if admin_user and "Password" not in admin_user:
                admin_user["Password"] = hash_password("admin123")
                modified = True
            
            demo_user = next((u for u in db["Users"] if u["Email"].lower() == "demo@user.com"), None)
            if demo_user and "Password" not in demo_user:
                demo_user["Password"] = hash_password("demo123")
                modified = True
            
            if modified:
                save_db()
                print("Backfilled missing passwords for seeded admin and user accounts in Python database.")
            
            print(f"Database loaded successfully and normalized from {DB_FILE}")
            return
        except Exception as e:
            print(f"Error reading DB_FILE, re-initializing... {e}")

    print("Initializing fresh database and seeding realistic demo data in Python...")
    # 1. Seed Users
    db["Users"] = [
        {
            "UserID": 1,
            "Name": "System Admin",
            "Email": "admin@demo.com",
            "Role": "admin",
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "Password": hash_password("admin123")
        },
        {
            "UserID": 2,
            "Name": "John Doe",
            "Email": "demo@user.com",
            "Role": "user",
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "Password": hash_password("demo123")
        }
    ]

    # 2. Seed Fitness Profile
    db["FitnessProfile"] = [
        {
            "UserID": 2,
            "Age": 28,
            "Gender": "Male",
            "Height": 180.0,
            "Weight": 82.0,
            "BMI": 25.31,
            "Experience": "Intermediate",
            "Goal": "Muscle Gain"
        }
    ]

    # 3. Seed Exercises with safety tips & alternatives
    db["Exercises"] = [
        {
            "ExerciseID": 1,
            "ExerciseName": "Bench Press",
            "MuscleGroup": "Chest",
            "Description": "A classic upper body compound exercise targeting the pectoral muscles, anterior deltoids, and triceps.",
            "SafetyTips": "Keep your feet flat on the floor, maintain a slight arch in your lower back, and do not flare your elbows excessively (aim for 45 degrees).",
            "Difficulty": "Intermediate",
            "Equipment": "Barbell, Bench",
            "Alternatives": ["Dumbbell Floor Press (Safer for shoulders)", "Incline Dumbbell Press (Reduces flat bench shoulder strain)"]
        },
        {
            "ExerciseID": 2,
            "ExerciseName": "Push-ups",
            "MuscleGroup": "Chest",
            "Description": "A versatile bodyweight movement that strengthens the chest, shoulders, and triceps while training core stability.",
            "SafetyTips": "Maintain a rigid plank position. Do not sag your hips or crane your neck forward.",
            "Difficulty": "Beginner",
            "Equipment": "Bodyweight",
            "Alternatives": ["Incline Push-ups (Easier on shoulders)", "Knee Push-ups (Regressed load)"]
        },
        {
            "ExerciseID": 3,
            "ExerciseName": "Pull-ups",
            "MuscleGroup": "Back",
            "Description": "An advanced upper body pulling exercise focusing on the latissimus dorsi, biceps, and upper back.",
            "SafetyTips": "Pull with your elbows, keep your shoulders depressed and retracted at the start, and control the eccentric (lowering) phase.",
            "Difficulty": "Advanced",
            "Equipment": "Pull-up Bar",
            "Alternatives": ["Lat Pulldown (Controls weight, easier to scale)", "Inverted Rows (Lower intensity pulling)"]
        },
        {
            "ExerciseID": 4,
            "ExerciseName": "Barbell Row",
            "MuscleGroup": "Back",
            "Description": "A powerful back exercise targeting the lats, rhomboids, traps, and rear delts, while requiring lower back stability.",
            "SafetyTips": "Keep a flat back, bend at the hips, and pull the bar to your lower rib cage. Avoid rounding your spine.",
            "Difficulty": "Intermediate",
            "Equipment": "Barbell",
            "Alternatives": ["Chest-Supported Row (Eliminates lower back load)", "Seated Cable Rows (Stable seated posture)"]
        },
        {
            "ExerciseID": 5,
            "ExerciseName": "Overhead Shoulder Press",
            "MuscleGroup": "Shoulders",
            "Description": "A fundamental vertical pushing movement that builds shoulder strength and stability.",
            "SafetyTips": "Keep your core engaged, glutes tight, and press in a straight line up. Avoid hyperextending your lower back.",
            "Difficulty": "Intermediate",
            "Equipment": "Barbell or Dumbbells",
            "Alternatives": ["Landmine Press (Safer arc-like vertical press)", "Dumbbell Shoulder Press (Independent shoulder tracking)"]
        },
        {
            "ExerciseID": 6,
            "ExerciseName": "Lateral Raises",
            "MuscleGroup": "Shoulders",
            "Description": "An isolation exercise targeting the lateral head of the deltoids to create shoulder width.",
            "SafetyTips": "Lead with your elbows and maintain a slight forward bend in your torso. Do not swing the weights.",
            "Difficulty": "Beginner",
            "Equipment": "Dumbbells",
            "Alternatives": ["Cable Lateral Raises (Continuous tension)", "Machine Lateral Raises (Guarded path of motion)"]
        },
        {
            "ExerciseID": 7,
            "ExerciseName": "Barbell Back Squat",
            "MuscleGroup": "Legs",
            "Description": "The king of lower body compound exercises, targeting the quadriceps, glutes, hamstrings, and lower back.",
            "SafetyTips": "Keep your heels flat, chest up, and push your knees outward. Descend until your thighs are parallel to the floor or lower.",
            "Difficulty": "Intermediate",
            "Equipment": "Barbell, Squat Rack",
            "Alternatives": ["Goblet Squat (Reduces spinal loading)", "Leg Press (Safer alternative for lower back issues)"]
        },
        {
            "ExerciseID": 8,
            "ExerciseName": "Romanian Deadlift",
            "MuscleGroup": "Legs",
            "Description": "An excellent hinge pattern exercise targeting the hamstrings, glutes, and posterior chain.",
            "SafetyTips": "Hinge at your hips, keep the weight close to your legs, and keep a flat spine. Stop when you feel a maximum stretch in hamstrings.",
            "Difficulty": "Intermediate",
            "Equipment": "Barbell or Dumbbells",
            "Alternatives": ["Leg Curls (Saves lower back while isolating hamstrings)", "Glute Bridges (Glute focus without back bending)"]
        },
        {
            "ExerciseID": 9,
            "ExerciseName": "Bicep Curl",
            "MuscleGroup": "Arms",
            "Description": "An isolation exercise focusing strictly on the biceps brachii.",
            "SafetyTips": "Keep your elbows pinned to your sides. Avoid swinging your body to lift the weight.",
            "Difficulty": "Beginner",
            "Equipment": "Dumbbells or Barbell",
            "Alternatives": ["Hammer Curls (Target brachioradialis)", "Preacher Curls (Eliminates cheating)"]
        },
        {
            "ExerciseID": 10,
            "ExerciseName": "Tricep Overhead Extension",
            "MuscleGroup": "Arms",
            "Description": "An exercise targeting the long head of the triceps by placing them in a deep stretch.",
            "SafetyTips": "Keep your upper arms vertical and close to your ears. Avoid flaring your elbows outward.",
            "Difficulty": "Beginner",
            "Equipment": "Dumbbell",
            "Alternatives": ["Cable Tricep Pushdowns (Safer elbow position)", "Dips (Compound arms/chest extension)"]
        },
        {
            "ExerciseID": 11,
            "ExerciseName": "Plank",
            "MuscleGroup": "Core",
            "Description": "An isometric core strength exercise that tests abdominal endurance and full-body rigidity.",
            "SafetyTips": "Squeeze your glutes and core, keep a straight line from your head to your heels, and do not let your lower back sag.",
            "Difficulty": "Beginner",
            "Equipment": "Bodyweight",
            "Alternatives": ["Deadbugs (Active dynamic core stability)", "Bird-Dog (Gentler lumbar loading)"]
        }
    ]

    def get_days_ago(days: int) -> str:
        d = datetime.date.today() - datetime.timedelta(days=days)
        return d.isoformat()

    # 4. Seed Workouts
    db["WorkoutHistory"] = [
        {
            "WorkoutID": 1,
            "UserID": 2,
            "Exercise": "Bench Press",
            "MuscleGroup": "Chest",
            "Weight": 80.0,
            "Sets": 4,
            "Reps": 8,
            "Duration": 45,
            "Difficulty": "Hard",
            "WorkoutDate": get_days_ago(10),
            "Notes": "Felt slight tightness in my right shoulder on the last set."
        },
        {
            "WorkoutID": 2,
            "UserID": 2,
            "Exercise": "Pull-ups",
            "MuscleGroup": "Back",
            "Weight": 0.0,
            "Sets": 3,
            "Reps": 10,
            "Duration": 30,
            "Difficulty": "Medium",
            "WorkoutDate": get_days_ago(9),
            "Notes": "Lats felt great. Controlled descent."
        },
        {
            "WorkoutID": 3,
            "UserID": 2,
            "Exercise": "Barbell Back Squat",
            "MuscleGroup": "Legs",
            "Weight": 100.0,
            "Sets": 4,
            "Reps": 6,
            "Duration": 50,
            "Difficulty": "Hard",
            "WorkoutDate": get_days_ago(8),
            "Notes": "Legs were fatigued but form felt solid."
        },
        {
            "WorkoutID": 4,
            "UserID": 2,
            "Exercise": "Overhead Shoulder Press",
            "MuscleGroup": "Shoulders",
            "Weight": 50.0,
            "Sets": 3,
            "Reps": 8,
            "Duration": 40,
            "Difficulty": "Hard",
            "WorkoutDate": get_days_ago(6),
            "Notes": "Right shoulder felt some pinching when pressing lockout."
        },
        {
            "WorkoutID": 5,
            "UserID": 2,
            "Exercise": "Bench Press",
            "MuscleGroup": "Chest",
            "Weight": 85.0,
            "Sets": 3,
            "Reps": 6,
            "Duration": 45,
            "Difficulty": "Very Hard",
            "WorkoutDate": get_days_ago(4),
            "Notes": "Shoulder pain became prominent on set 3. Had to stop."
        },
        {
            "WorkoutID": 6,
            "UserID": 2,
            "Exercise": "Bicep Curl",
            "MuscleGroup": "Arms",
            "Weight": 15.0,
            "Sets": 3,
            "Reps": 12,
            "Duration": 20,
            "Difficulty": "Medium",
            "WorkoutDate": get_days_ago(2),
            "Notes": "Arm accessory day. Quick pump."
        }
    ]

    # 5. Seed Pain Reports
    db["PainReports"] = [
        {
            "PainID": 1,
            "UserID": 2,
            "BodyPart": "Shoulder",
            "Exercise": "Bench Press",
            "PainLevel": 6,
            "PainType": "Sharp pinching",
            "Duration": "3 days",
            "Notes": "Pinched feeling in front of right shoulder at the bottom of the bench press. Stiff the next morning.",
            "ReportDate": get_days_ago(3)
        }
    ]

    # 6. Seed Recommendation
    db["AIRecommendations"] = [
        {
            "RecommendationID": 1,
            "UserID": 2,
            "PainID": 1,
            "Recommendation": "Based on your report of sharp pinching in your Shoulder during Bench Press, you may be experiencing minor rotator cuff impingement...\n\n**Possible Causes:**\n- Too much shoulder internal rotation or flaring elbow position.\n- High training volume with insufficient back pulling.\n\n**Recommendations:**\n1. Substitute Bench Press with Dumbbell Floor Press.\n2. Keep elbows angled at 45 degrees.\n3. Rotator cuff band warm-ups.\n4. Rest shoulder pressing for 7 days.",
            "RiskLevel": "Medium",
            "CreatedAt": (datetime.datetime.utcnow() - datetime.timedelta(days=3)).isoformat() + "Z"
        }
    ]

    # 7. Seed Recovery Plan
    db["RecoveryPlans"] = [
        {
            "RecoveryID": 1,
            "UserID": 2,
            "Advice": "Rest shoulder from pressing exercises, perform rotator cuff stretches and band wall walks.",
            "RecoveryDays": 7,
            "Status": "Active"
        }
    ]

    # 8. Seed Notifications
    db["Notifications"] = [
        {
            "NotificationID": 1,
            "UserID": 2,
            "Title": "Welcome to Injury Prevention Assistant!",
            "Message": "Complete your fitness profile to enable personalized injury risk calculations and AI recommended alternatives!",
            "Status": "unread",
            "IsAnnouncement": False,
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z"
        },
        {
            "NotificationID": 2,
            "UserID": None,
            "Title": "System Announcement: Safety Guidelines",
            "Message": "Always warm up for at least 5-10 minutes prior to lifting heavy loads to protect tendons and dynamic stabilizers.",
            "Status": "unread",
            "IsAnnouncement": True,
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
    ]

    save_db()

class DBService:
    @staticmethod
    def ensure_ready():
        if not db["Users"]:
            init_db()

    # Users
    @staticmethod
    def get_users() -> List[Dict[str, Any]]:
        return db["Users"]

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        return next((u for u in db["Users"] if u["UserID"] == user_id), None)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        return next((u for u in db["Users"] if u["Email"].lower() == email.lower()), None)

    @staticmethod
    def create_user(name: str, email: str, password_hash: str, role: str = "user") -> Dict[str, Any]:
        next_id = max([u["UserID"] for u in db["Users"]] or [0]) + 1
        new_user = {
            "UserID": next_id,
            "Name": name,
            "Email": email,
            "Role": role,
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "Password": password_hash
        }
        db["Users"].append(new_user)
        save_db()
        return new_user

    @staticmethod
    def update_user_password(user_id: int, new_hash: str) -> bool:
        user = DBService.get_user_by_id(user_id)
        if user:
            user["Password"] = new_hash
            save_db()
            return True
        return False

    @staticmethod
    def delete_user(user_id: int) -> bool:
        db["Users"] = [u for u in db["Users"] if u["UserID"] != user_id]
        db["FitnessProfile"] = [p for p in db["FitnessProfile"] if p["UserID"] != user_id]
        db["WorkoutHistory"] = [w for w in db["WorkoutHistory"] if w["UserID"] != user_id]
        db["PainReports"] = [pr for pr in db["PainReports"] if pr["UserID"] != user_id]
        db["AIRecommendations"] = [r for r in db["AIRecommendations"] if r["UserID"] != user_id]
        db["RecoveryPlans"] = [rp for rp in db["RecoveryPlans"] if rp["UserID"] != user_id]
        db["ChatHistory"] = [ch for ch in db["ChatHistory"] if ch["UserID"] != user_id]
        db["Notifications"] = [n for n in db["Notifications"] if n["UserID"] != user_id]
        db["PasswordReset"] = [p for p in db["PasswordReset"] if p["UserID"] != user_id]
        save_db()
        return True

    # Fitness Profile
    @staticmethod
    def get_profile_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
        return next((p for p in db["FitnessProfile"] if p["UserID"] == user_id), None)

    @staticmethod
    def upsert_profile(user_id: int, age: int, gender: str, height: float, weight: float, experience: str, goal: str) -> Dict[str, Any]:
        existing = DBService.get_profile_by_user_id(user_id)
        bmi = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0.0

        if existing:
            existing["Age"] = age
            existing["Gender"] = gender
            existing["Height"] = height
            existing["Weight"] = weight
            existing["BMI"] = bmi
            existing["Experience"] = experience
            existing["Goal"] = goal
        else:
            next_id = max([p.get("ProfileID", 0) for p in db["FitnessProfile"]] or [0]) + 1
            existing = {
                "ProfileID": next_id,
                "UserID": user_id,
                "Age": age,
                "Gender": gender,
                "Height": height,
                "Weight": weight,
                "BMI": bmi,
                "Experience": experience,
                "Goal": goal
            }
            db["FitnessProfile"].append(existing)
        save_db()
        return existing

    # Exercises
    @staticmethod
    def get_exercises() -> List[Dict[str, Any]]:
        return db["Exercises"]

    @staticmethod
    def get_exercise_by_id(exercise_id: int) -> Optional[Dict[str, Any]]:
        return next((e for e in db["Exercises"] if e["ExerciseID"] == exercise_id), None)

    @staticmethod
    def get_exercise_by_name(name: str) -> Optional[Dict[str, Any]]:
        return next((e for e in db["Exercises"] if e["ExerciseName"].lower() == name.lower()), None)

    @staticmethod
    def create_exercise(exercise_name: str, muscle_group: str, description: str, safety_tips: str, difficulty: str, equipment: str, alternatives: List[str]) -> Dict[str, Any]:
        next_id = max([e["ExerciseID"] for e in db["Exercises"]] or [0]) + 1
        new_ex = {
            "ExerciseID": next_id,
            "ExerciseName": exercise_name,
            "MuscleGroup": muscle_group,
            "Description": description,
            "SafetyTips": safety_tips,
            "Difficulty": difficulty,
            "Equipment": equipment,
            "Alternatives": alternatives
        }
        db["Exercises"].append(new_ex)
        save_db()
        return new_ex

    @staticmethod
    def update_exercise(exercise_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ex = DBService.get_exercise_by_id(exercise_id)
        if ex:
            for k, v in data.items():
                if k in ex:
                    ex[k] = v
            save_db()
            return ex
        return None

    @staticmethod
    def delete_exercise(exercise_id: int) -> bool:
        db["Exercises"] = [e for e in db["Exercises"] if e["ExerciseID"] != exercise_id]
        save_db()
        return True

    # Workout History
    @staticmethod
    def get_workouts_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        workouts = [w for w in db["WorkoutHistory"] if w["UserID"] == user_id]
        return sorted(workouts, key=lambda x: x["WorkoutDate"], reverse=True)

    @staticmethod
    def create_workout(user_id: int, exercise: str, muscle_group: str, weight: float, sets: int, reps: int, duration: int, difficulty: str, workout_date: str, notes: str) -> Dict[str, Any]:
        next_id = max([w["WorkoutID"] for w in db["WorkoutHistory"]] or [0]) + 1
        new_workout = {
            "WorkoutID": next_id,
            "UserID": user_id,
            "Exercise": exercise,
            "MuscleGroup": muscle_group,
            "Weight": float(weight),
            "Sets": int(sets),
            "Reps": int(reps),
            "Duration": int(duration),
            "Difficulty": difficulty,
            "WorkoutDate": workout_date or datetime.date.today().isoformat(),
            "Notes": notes
        }
        db["WorkoutHistory"].append(new_workout)
        save_db()
        return new_workout

    @staticmethod
    def update_workout(workout_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        w = next((item for item in db["WorkoutHistory"] if item["WorkoutID"] == workout_id), None)
        if w:
            for k, v in data.items():
                if k in w:
                    if k in ["Weight"]:
                        w[k] = float(v)
                    elif k in ["Sets", "Reps", "Duration"]:
                        w[k] = int(v)
                    else:
                        w[k] = v
            save_db()
            return w
        return None

    @staticmethod
    def delete_workout(workout_id: int) -> bool:
        db["WorkoutHistory"] = [w for w in db["WorkoutHistory"] if w["WorkoutID"] != workout_id]
        save_db()
        return True

    # Pain Reports
    @staticmethod
    def get_pain_reports_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        reports = [p for p in db["PainReports"] if p["UserID"] == user_id]
        # Sort by ReportDate desc, then PainID desc
        return sorted(reports, key=lambda x: (x["ReportDate"], x["PainID"]), reverse=True)

    @staticmethod
    def create_pain_report(user_id: int, body_part: str, exercise: str, pain_level: int, pain_type: str, duration: str, notes: str, report_date: str) -> Dict[str, Any]:
        next_id = max([p["PainID"] for p in db["PainReports"]] or [0]) + 1
        new_report = {
            "PainID": next_id,
            "UserID": user_id,
            "BodyPart": body_part,
            "Exercise": exercise,
            "PainLevel": int(pain_level),
            "PainType": pain_type,
            "Duration": duration,
            "Notes": notes,
            "ReportDate": report_date or datetime.date.today().isoformat()
        }
        db["PainReports"].append(new_report)
        save_db()
        return new_report

    @staticmethod
    def update_pain_report(pain_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        p = next((item for item in db["PainReports"] if item["PainID"] == pain_id), None)
        if p:
            for k, v in data.items():
                if k in p:
                    if k == "PainLevel":
                        p[k] = int(v)
                    else:
                        p[k] = v
            save_db()
            return p
        return None

    @staticmethod
    def delete_pain_report(pain_id: int) -> bool:
        db["PainReports"] = [p for p in db["PainReports"] if p["PainID"] != pain_id]
        save_db()
        return True

    # AI Recommendations
    @staticmethod
    def get_recommendations_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        recs = [r for r in db["AIRecommendations"] if r["UserID"] == user_id]
        return sorted(recs, key=lambda x: x["CreatedAt"], reverse=True)

    @staticmethod
    def create_recommendation(user_id: int, pain_id: Optional[int], recommendation: str, risk_level: str) -> Dict[str, Any]:
        next_id = max([r["RecommendationID"] for r in db["AIRecommendations"]] or [0]) + 1
        new_rec = {
            "RecommendationID": next_id,
            "UserID": user_id,
            "PainID": pain_id,
            "Recommendation": recommendation,
            "RiskLevel": risk_level,
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db["AIRecommendations"].append(new_rec)
        save_db()
        return new_rec

    @staticmethod
    def delete_recommendation(rec_id: int) -> bool:
        db["AIRecommendations"] = [r for r in db["AIRecommendations"] if r["RecommendationID"] != rec_id]
        save_db()
        return True

    # Chat History
    @staticmethod
    def get_chat_history_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        chats = [ch for ch in db["ChatHistory"] if ch["UserID"] == user_id]
        return sorted(chats, key=lambda x: x["Timestamp"])

    @staticmethod
    def add_chat_message(user_id: int, question: str, response: str) -> Dict[str, Any]:
        next_id = max([ch["ChatID"] for ch in db["ChatHistory"]] or [0]) + 1
        new_message = {
            "ChatID": next_id,
            "UserID": user_id,
            "Question": question,
            "Response": response,
            "Timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db["ChatHistory"].append(new_message)
        save_db()
        return new_message

    # Notifications
    @staticmethod
    def get_notifications_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        notifs = [n for n in db["Notifications"] if n["UserID"] == user_id or n["UserID"] is None]
        # Map IsRead based on Status
        result = []
        for n in notifs:
            n_copy = dict(n)
            n_copy["IsRead"] = (n["Status"] == "read")
            result.append(n_copy)
        return sorted(result, key=lambda x: x["CreatedAt"], reverse=True)

    @staticmethod
    def get_unread_notifications_count(user_id: int) -> int:
        return len([n for n in db["Notifications"] if (n["UserID"] == user_id or n["UserID"] is None) and n["Status"] == "unread"])

    @staticmethod
    def create_notification(user_id: Optional[int], title: str, message: str, is_announcement: bool = False) -> Dict[str, Any]:
        next_id = max([n["NotificationID"] for n in db["Notifications"]] or [0]) + 1
        new_notif = {
            "NotificationID": next_id,
            "UserID": user_id,
            "Title": title,
            "Message": message,
            "Status": "unread",
            "IsAnnouncement": is_announcement,
            "CreatedAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db["Notifications"].append(new_notif)
        save_db()
        return new_notif

    @staticmethod
    def mark_notification_as_read(notif_id: int) -> bool:
        notif = next((n for n in db["Notifications"] if n["NotificationID"] == notif_id), None)
        if notif:
            notif["Status"] = "read"
            save_db()
            return True
        return False

    # Password Reset
    @staticmethod
    def create_password_reset(user_id: int, otp: str) -> Dict[str, Any]:
        expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        next_id = max([p["ResetID"] for p in db["PasswordReset"]] or [0]) + 1
        new_reset = {
            "ResetID": next_id,
            "UserID": user_id,
            "OTP": otp,
            "Expiry": expiry.isoformat() + "Z"
        }
        db["PasswordReset"].append(new_reset)
        save_db()
        return new_reset

    @staticmethod
    def verify_reset_otp(user_id: int, otp: str) -> bool:
        # Check entries matching user and otp, check expiry
        now = datetime.datetime.utcnow().isoformat() + "Z"
        entry = next((p for p in db["PasswordReset"] if p["UserID"] == user_id and p["OTP"] == otp and p["Expiry"] > now), None)
        if entry:
            db["PasswordReset"] = [p for p in db["PasswordReset"] if p["UserID"] != user_id]
            save_db()
            return True
        return False

    # Activity Logs
    @staticmethod
    def get_activity_logs() -> List[Dict[str, Any]]:
        return sorted(db["ActivityLog"], key=lambda x: x["Time"], reverse=True)

    @staticmethod
    def log_activity(user_id: Optional[int], activity: str):
        next_id = max([l["LogID"] for l in db["ActivityLog"]] or [0]) + 1
        log = {
            "LogID": next_id,
            "UserID": user_id,
            "Activity": activity,
            "Time": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db["ActivityLog"].append(log)
        save_db()

    # Admin Statistics
    @staticmethod
    def get_admin_stats() -> Dict[str, Any]:
        total_users = len([u for u in db["Users"] if u["Role"] == "user"])
        total_workouts = len(db["WorkoutHistory"])
        total_pain_reports = len(db["PainReports"])

        risk_levels = {"Low": 0, "Medium": 0, "High": 0}
        for u in db["Users"]:
            if u["Role"] == "admin":
                continue
            recs = [r for r in db["AIRecommendations"] if r["UserID"] == u["UserID"]]
            if recs:
                # Sort by CreatedAt desc
                recs_sorted = sorted(recs, key=lambda x: x["CreatedAt"], reverse=True)
                rl = recs_sorted[0]["RiskLevel"]
                if rl == "High":
                    risk_levels["High"] += 1
                elif rl == "Medium":
                    risk_levels["Medium"] += 1
                else:
                    risk_levels["Low"] += 1
            else:
                risk_levels["Low"] += 1

        return {
            "totalUsers": total_users,
            "totalWorkouts": total_workouts,
            "totalPainReports": total_pain_reports,
            "riskDistribution": [
                {"name": "Low Risk", "value": risk_levels["Low"]},
                {"name": "Medium Risk", "value": risk_levels["Medium"]},
                {"name": "High Risk", "value": risk_levels["High"]}
            ]
        }
