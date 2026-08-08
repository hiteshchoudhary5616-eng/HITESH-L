import os
import random
import datetime
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional

# Load local modules
from python_backend.db import DBService, hash_password, check_password
from python_backend.risk_engine import calculate_injury_risk
from python_backend.ai_service import generate_analysis, chat_reply

# Initialize database
DBService.ensure_ready()

app = FastAPI(title="AI Injury Prevention Assistant Backend", version="1.0.0")

# Enable CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized. Missing authentication token.")
    
    token = authorization.split(" ")[1]
    try:
        user_id = int(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
    
    user = DBService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist.")
    return user

async def get_admin_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("Role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Administrator privileges required.")
    return user

# Pydantic schemas for requests
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str

class ProfileRequest(BaseModel):
    age: int
    gender: str
    height: float
    weight: float
    experience: str
    goal: str

class WorkoutRequest(BaseModel):
    exercise: str
    muscleGroup: str
    weight: float
    sets: int
    reps: int
    duration: int
    difficulty: str
    workoutDate: Optional[str] = None
    notes: Optional[str] = ""

class PainReportRequest(BaseModel):
    bodyPart: str
    exercise: Optional[str] = "None"
    painLevel: int
    painType: str
    duration: str
    notes: Optional[str] = ""
    reportDate: Optional[str] = None

class ChatRequest(BaseModel):
    question: str

class AnnouncementRequest(BaseModel):
    title: str
    message: str

class ExerciseRequest(BaseModel):
    exerciseName: str
    muscleGroup: str
    description: Optional[str] = "Custom user-created workout."
    safetyTips: Optional[str] = "Maintain steady biomechanics and proper form."
    difficulty: Optional[str] = "Intermediate"
    equipment: Optional[str] = "None"
    alternatives: Optional[list] = []

# ============================================================================
# API ENDPOINTS
# ============================================================================

# 1. Authentication Endpoints
@app.post("/api/auth/register", status_code=201)
async def register(req: RegisterRequest):
    existing = DBService.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
    
    pwd_hash = hash_password(req.password)
    new_user = DBService.create_user(req.name, req.email, pwd_hash)
    
    DBService.log_activity(new_user["UserID"], "User registered account")
    
    # Create welcome notification
    DBService.create_notification(
        user_id=new_user["UserID"],
        title="Welcome aboard!",
        message=f"Hi {req.name}, welcome to the AI Injury Prevention Assistant. Complete your fitness profile to get detailed biomechanical injury risk scoring!"
    )
    
    # Filter password out of response
    res_user = dict(new_user)
    res_user.pop("Password", None)
    
    return {
        "token": str(new_user["UserID"]),
        "user": res_user
    }

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = DBService.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    stored_hash = user.get("Password", "")
    if not check_password(req.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    DBService.log_activity(user["UserID"], "User logged in successfully")
    
    res_user = {
        "UserID": user["UserID"],
        "Name": user["Name"],
        "Email": user["Email"],
        "Role": user["Role"]
    }
    
    return {
        "token": str(user["UserID"]),
        "user": res_user
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    user = DBService.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    
    # Generate numeric 6-digit OTP
    otp = str(random.randint(100000, 999999))
    DBService.create_password_reset(user["UserID"], otp)
    DBService.log_activity(user["UserID"], f"Generated password reset OTP: {otp}")
    
    return {
        "message": "Password reset code generated.",
        "otp": otp # Displayed directly to client for demo purposes
    }

@app.post("/api/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    user = DBService.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
    
    is_valid = DBService.verify_reset_otp(user["UserID"], req.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP reset code.")
        
    new_hash = hash_password(req.newPassword)
    DBService.update_user_password(user["UserID"], new_hash)
    DBService.log_activity(user["UserID"], "Password reset successfully via OTP")
    
    return {"message": "Password has been reset successfully."}

@app.post("/api/auth/change-password")
async def change_password(req: ChangePasswordRequest, user: Dict[str, Any] = Depends(get_current_user)):
    stored_hash = user.get("Password", "")
    if not check_password(req.currentPassword, stored_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
        
    new_hash = hash_password(req.newPassword)
    DBService.update_user_password(user["UserID"], new_hash)
    DBService.log_activity(user["UserID"], "User changed account password")
    
    return {"message": "Password updated successfully."}

# 2. Profile Endpoints
@app.get("/api/profile")
async def get_profile(user: Dict[str, Any] = Depends(get_current_user)):
    profile = DBService.get_profile_by_user_id(user["UserID"])
    return profile

@app.put("/api/profile")
async def update_profile(req: ProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    profile = DBService.upsert_profile(
        user_id=user["UserID"],
        age=req.age,
        gender=req.gender,
        height=req.height,
        weight=req.weight,
        experience=req.experience,
        goal=req.goal
    )
    DBService.log_activity(user["UserID"], f"Updated fitness profile (BMI: {profile.get('BMI')})")
    return profile

# 3. Workout Tracker Endpoints
@app.get("/api/workouts")
async def get_workouts(user: Dict[str, Any] = Depends(get_current_user)):
    return DBService.get_workouts_by_user_id(user["UserID"])

@app.post("/api/workouts", status_code=201)
async def log_workout(req: WorkoutRequest, user: Dict[str, Any] = Depends(get_current_user)):
    workout = DBService.create_workout(
        user_id=user["UserID"],
        exercise=req.exercise,
        muscle_group=req.muscleGroup,
        weight=req.weight,
        sets=req.sets,
        reps=req.reps,
        duration=req.duration,
        difficulty=req.difficulty,
        workout_date=req.workoutDate,
        notes=req.notes
    )
    DBService.log_activity(user["UserID"], f"Logged workout: {req.exercise} ({req.sets}x{req.reps})")
    return workout

@app.put("/api/workouts/{workout_id}")
async def update_workout(workout_id: int, req: WorkoutRequest, user: Dict[str, Any] = Depends(get_current_user)):
    # Make dictionary update
    update_data = req.dict(exclude_unset=True)
    # Map camelCase to PascalCase if they exist in schema
    mapped = {
        "Exercise": update_data.get("exercise"),
        "MuscleGroup": update_data.get("muscleGroup"),
        "Weight": update_data.get("weight"),
        "Sets": update_data.get("sets"),
        "Reps": update_data.get("reps"),
        "Duration": update_data.get("duration"),
        "Difficulty": update_data.get("difficulty"),
        "WorkoutDate": update_data.get("workoutDate"),
        "Notes": update_data.get("notes")
    }
    mapped = {k: v for k, v in mapped.items() if v is not None}
    
    updated = DBService.update_workout(workout_id, mapped)
    if not updated:
        raise HTTPException(status_code=404, detail="Workout not found.")
        
    DBService.log_activity(user["UserID"], f"Updated workout ID {workout_id}")
    return updated

@app.delete("/api/workouts/{workout_id}")
async def delete_workout(workout_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    DBService.delete_workout(workout_id)
    DBService.log_activity(user["UserID"], f"Deleted workout ID {workout_id}")
    return {"message": "Workout deleted successfully."}

# 4. Pain Assessment Endpoints
@app.get("/api/pain-reports")
async def get_pain_reports(user: Dict[str, Any] = Depends(get_current_user)):
    return DBService.get_pain_reports_by_user_id(user["UserID"])

@app.post("/api/pain-reports", status_code=201)
async def log_pain_report(req: PainReportRequest, user: Dict[str, Any] = Depends(get_current_user)):
    report = DBService.create_pain_report(
        user_id=user["UserID"],
        body_part=req.bodyPart,
        exercise=req.exercise,
        pain_level=req.painLevel,
        pain_type=req.painType,
        duration=req.duration,
        notes=req.notes,
        report_date=req.reportDate
    )
    
    DBService.log_activity(user["UserID"], f"Logged pain report: {req.bodyPart} (Level {req.painLevel}/10)")
    
    if req.painLevel >= 6:
        DBService.create_notification(
            user_id=user["UserID"],
            title=f"High Pain Level Warning: {req.bodyPart}",
            message=f"You reported a Level {req.painLevel} pain for your {req.bodyPart}. We strongly suggest running an AI Injury Risk Analysis and resting from heavy sets."
        )
        
    return report

@app.put("/api/pain-reports/{pain_id}")
async def update_pain_report(pain_id: int, req: PainReportRequest, user: Dict[str, Any] = Depends(get_current_user)):
    update_data = req.dict(exclude_unset=True)
    mapped = {
        "BodyPart": update_data.get("bodyPart"),
        "Exercise": update_data.get("exercise"),
        "PainLevel": update_data.get("painLevel"),
        "PainType": update_data.get("painType"),
        "Duration": update_data.get("duration"),
        "Notes": update_data.get("notes"),
        "ReportDate": update_data.get("reportDate")
    }
    mapped = {k: v for k, v in mapped.items() if v is not None}
    
    updated = DBService.update_pain_report(pain_id, mapped)
    if not updated:
        raise HTTPException(status_code=404, detail="Pain report not found.")
        
    DBService.log_activity(user["UserID"], f"Updated pain report ID {pain_id}")
    return updated

@app.delete("/api/pain-reports/{pain_id}")
async def delete_pain_report(pain_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    DBService.delete_pain_report(pain_id)
    DBService.log_activity(user["UserID"], f"Deleted pain report ID {pain_id}")
    return {"message": "Pain report deleted successfully."}

# 5. AI Analysis Endpoints
@app.get("/api/ai/history")
async def get_ai_history(user: Dict[str, Any] = Depends(get_current_user)):
    return DBService.get_recommendations_by_user_id(user["UserID"])

@app.post("/api/ai/analyze")
async def analyze_injury_logs(user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user["UserID"]
    profile = DBService.get_profile_by_user_id(user_id)
    workouts = DBService.get_workouts_by_user_id(user_id)
    pain_reports = DBService.get_pain_reports_by_user_id(user_id)
    
    result = await generate_analysis(profile, workouts, pain_reports)
    
    latest_pain = pain_reports[0]["PainID"] if pain_reports else None
    saved_rec = DBService.create_recommendation(
        user_id=user_id,
        pain_id=latest_pain,
        recommendation=json.dumps(result), # Store fully structured as JSON string
        risk_level=result["riskLevel"]
    )
    
    DBService.log_activity(user_id, f"Triggered AI Injury Risk Analysis (Risk: {result['riskLevel']})")
    
    # Send notification
    alts = result.get("saferAlternatives", [])
    alt_text = ", ".join(alts[:2]) if alts else "None"
    DBService.create_notification(
        user_id=user_id,
        title="AI Safety Analysis Complete",
        message=f"Your Injury Risk is estimated as {result['riskLevel']}. Alternatives recommended: {alt_text}."
    )
    
    return saved_rec

# 6. Exercise Library Endpoints
@app.get("/api/exercises")
async def list_exercises(category: Optional[str] = Query(None), search: Optional[str] = Query(None)):
    exercises = DBService.get_exercises()
    
    if category:
        exercises = [e for e in exercises if e["MuscleGroup"].lower() == category.lower()]
        
    if search:
        q = search.lower()
        exercises = [e for e in exercises if q in e["ExerciseName"].lower() or q in e["Description"].lower()]
        
    return exercises

@app.get("/api/exercises/{exercise_id}")
async def get_exercise_details(exercise_id: int):
    ex = DBService.get_exercise_by_id(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found.")
    return ex

@app.post("/api/exercises", status_code=201)
async def create_custom_exercise(req: ExerciseRequest, user: Dict[str, Any] = Depends(get_current_user)):
    new_ex = DBService.create_exercise(
        exercise_name=req.exerciseName,
        muscle_group=req.muscleGroup,
        description=req.description,
        safety_tips=req.safetyTips,
        difficulty=req.difficulty,
        equipment=req.equipment,
        alternatives=req.alternatives
    )
    DBService.log_activity(user["UserID"], f"User created exercise: {req.exerciseName}")
    return new_ex

# 7. Injury Risk Score Endpoint
@app.get("/api/risk/current")
async def get_current_risk(user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user["UserID"]
    profile = DBService.get_profile_by_user_id(user_id)
    workouts = DBService.get_workouts_by_user_id(user_id)
    pain_reports = DBService.get_pain_reports_by_user_id(user_id)
    
    score = calculate_injury_risk(workouts, pain_reports, profile)
    return score

# 8. AI Chatbot Endpoints
@app.get("/api/chat/history")
async def get_chat_history(user: Dict[str, Any] = Depends(get_current_user)):
    return DBService.get_chat_history_by_user_id(user["UserID"])

@app.post("/api/chat")
async def chat_message(req: ChatRequest, user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user["UserID"]
    profile = DBService.get_profile_by_user_id(user_id)
    workouts = DBService.get_workouts_by_user_id(user_id)
    pain_reports = DBService.get_pain_reports_by_user_id(user_id)
    
    answer = await chat_reply(profile, workouts, pain_reports, req.question)
    message_obj = DBService.add_chat_message(user_id, req.question, answer)
    return message_obj

# 9. Notifications Endpoints
@app.get("/api/notifications")
async def get_notifications(user: Dict[str, Any] = Depends(get_current_user)):
    return DBService.get_notifications_by_user_id(user["UserID"])

@app.patch("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    success = DBService.mark_notification_as_read(notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"success": True}

# 10. Unified Dashboard Payload Endpoint
@app.get("/api/dashboard")
async def get_dashboard(user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user["UserID"]
    profile = DBService.get_profile_by_user_id(user_id)
    workouts = DBService.get_workouts_by_user_id(user_id)
    pain_reports = DBService.get_pain_reports_by_user_id(user_id)
    
    risk_assessment = calculate_injury_risk(workouts, pain_reports, profile)
    recent_recs = DBService.get_recommendations_by_user_id(user_id)
    unread_count = DBService.get_unread_notifications_count(user_id)
    
    # --- MODULE 10 Rule-Based Warnings ---
    # 1. Overtraining check
    consecutive_days = 0
    workout_dates = sorted(list({w["WorkoutDate"] for w in workouts}), reverse=True)
    if workout_dates:
        check_date = datetime.date.today()
        for _ in range(7):
            date_str = check_date.isoformat()
            if date_str in workout_dates:
                consecutive_days += 1
                check_date -= datetime.timedelta(days=1)
            else:
                break
                
    existing_notifs = DBService.get_notifications_by_user_id(user_id)
    def has_notification(title: str) -> bool:
        return any(n["Title"] == title for n in existing_notifs)
        
    if consecutive_days >= 3 and not has_notification("Rest Recommended Tomorrow"):
        DBService.create_notification(
            user_id=user_id,
            title="Rest Recommended Tomorrow",
            message=f"You have trained for {consecutive_days} consecutive days. Muscle fibers rebuild during rest. Take a day off tomorrow!"
        )
        
    # 2. High Pain recovery reminder
    if pain_reports and pain_reports[0]["PainLevel"] >= 5 and not has_notification("Recovery Reminder: Focus on Mobility"):
        try:
            pain_date = datetime.datetime.strptime(pain_reports[0]["ReportDate"].split("T")[0], "%Y-%m-%d")
            pain_age_days = (datetime.datetime.now() - pain_date).days
            if pain_age_days <= 3:
                DBService.create_notification(
                    user_id=user_id,
                    title="Recovery Reminder: Focus on Mobility",
                    message=f"You logged an active pain of {pain_reports[0]['PainLevel']}/10 for your {pain_reports[0]['BodyPart']} recently. Prioritize 15 minutes of dedicated dynamic stretching and mobility exercises today."
                )
        except Exception as e:
            print(f"Dashboard pain report warning parsing error: {e}")
            
    # 3. No workouts logged in 3 days
    if workouts and not has_notification("Ready to stretch and sweat?"):
        try:
            last_workout_date = datetime.datetime.strptime(workouts[0]["WorkoutDate"].split("T")[0], "%Y-%m-%d")
            days_since_workout = (datetime.datetime.now() - last_workout_date).days
            if days_since_workout >= 3:
                DBService.create_notification(
                    user_id=user_id,
                    title="Ready to stretch and sweat?",
                    message="It has been over 3 days since your last logged workout. If you are resting injuries, focus on core or low-impact cardio!"
                )
        except Exception as e:
            print(f"Dashboard last workout date warning parsing error: {e}")
            
    # Reconstruct Weekly Volume Chart Data (Last 7 Days)
    weekly_volume_data = []
    for i in range(6, -1, -1):
        target_date = datetime.date.today() - datetime.timedelta(days=i)
        date_str = target_date.isoformat()
        day_name = target_date.strftime("%a")
        
        day_workouts = [w for w in workouts if w["WorkoutDate"].split("T")[0] == date_str]
        day_vol = sum(float(w["Weight"]) * int(w["Sets"]) * int(w["Reps"]) for w in day_workouts)
        
        weekly_volume_data.append({
            "day": f"{day_name} ({target_date.day})",
            "volume": day_vol
        })
        
    # Muscle Distribution Data
    muscles = ["Chest", "Back", "Shoulders", "Legs", "Arms", "Core"]
    muscle_distribution_data = [
        {"muscle": m, "count": len([w for w in workouts if w["MuscleGroup"].lower() == m.lower()])}
        for m in muscles
    ]
    
    # Pain Trend Data (MM/DD format chronologically)
    pain_trend_data = []
    for p in pain_reports[:10]:
        try:
            parts = p["ReportDate"].split("-")
            # MM/DD format
            mm_dd = f"{parts[1]}/{parts[2]}" if len(parts) >= 3 else p["ReportDate"]
            pain_trend_data.append({
                "date": mm_dd,
                "level": p["PainLevel"]
            })
        except:
            pain_trend_data.append({
                "date": p["ReportDate"],
                "level": p["PainLevel"]
            })
    pain_trend_data.reverse() # chronologically oldest to newest
    
    res_user = {
        "UserID": user["UserID"],
        "Name": user["Name"],
        "Email": user["Email"],
        "Role": user["Role"]
    }
    
    return {
        "user": res_user,
        "profile": profile,
        "recentWorkouts": workouts[:5],
        "recentPainReports": pain_reports[:5],
        "riskAssessment": risk_assessment,
        "recentRecommendations": recent_recs[:3],
        "unreadNotificationsCount": DBService.get_unread_notifications_count(user_id),
        "weeklyVolumeData": weekly_volume_data,
        "muscleDistributionData": muscle_distribution_data,
        "painTrendData": pain_trend_data
    }

# ============================================================================
# ADMIN ONLY BLUEPRINT ENDPOINTS
# ============================================================================
@app.get("/api/admin/stats")
async def get_admin_stats(admin: Dict[str, Any] = Depends(get_admin_user)):
    stats = DBService.get_admin_stats()
    activity_logs = DBService.get_activity_logs()[:50]
    return {
        "stats": stats,
        "activityLogs": activity_logs
    }

@app.get("/api/admin/users")
async def list_admin_users(admin: Dict[str, Any] = Depends(get_admin_user)):
    users = DBService.get_users()
    res_users = []
    for u in users:
        if u["Role"] != "admin":
            res_user = dict(u)
            res_user.pop("Password", None)
            res_users.append(res_user)
    return res_users

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: Dict[str, Any] = Depends(get_admin_user)):
    DBService.delete_user(user_id)
    DBService.log_activity(admin["UserID"], f"Administrator deleted user account ID {user_id}")
    return {"success": True, "message": "User deleted successfully."}

@app.post("/api/admin/exercises", status_code=201)
async def admin_create_exercise(req: ExerciseRequest, admin: Dict[str, Any] = Depends(get_admin_user)):
    new_ex = DBService.create_exercise(
        exercise_name=req.exerciseName,
        muscle_group=req.muscleGroup,
        description=req.description,
        safety_tips=req.safetyTips,
        difficulty=req.difficulty,
        equipment=req.equipment,
        alternatives=req.alternatives
    )
    DBService.log_activity(admin["UserID"], f"Administrator created exercise: {req.exerciseName}")
    return new_ex

@app.put("/api/admin/exercises/{exercise_id}")
async def admin_update_exercise(exercise_id: int, req: ExerciseRequest, admin: Dict[str, Any] = Depends(get_admin_user)):
    update_data = req.dict(exclude_unset=True)
    # Map camelCase to PascalCase if they exist in schema
    mapped = {
        "ExerciseName": update_data.get("exerciseName"),
        "MuscleGroup": update_data.get("muscleGroup"),
        "Description": update_data.get("description"),
        "SafetyTips": update_data.get("safetyTips"),
        "Difficulty": update_data.get("difficulty"),
        "Equipment": update_data.get("equipment"),
        "Alternatives": update_data.get("alternatives")
    }
    mapped = {k: v for k, v in mapped.items() if v is not None}
    
    updated = DBService.update_exercise(exercise_id, mapped)
    if not updated:
        raise HTTPException(status_code=404, detail="Exercise not found.")
        
    DBService.log_activity(admin["UserID"], f"Administrator updated exercise ID {exercise_id}")
    return updated

@app.delete("/api/admin/exercises/{exercise_id}")
async def admin_delete_exercise(exercise_id: int, admin: Dict[str, Any] = Depends(get_admin_user)):
    DBService.delete_exercise(exercise_id)
    DBService.log_activity(admin["UserID"], f"Administrator deleted exercise ID {exercise_id}")
    return {"success": True}

@app.delete("/api/admin/pain-reports/{pain_id}")
async def admin_delete_pain_report(pain_id: int, admin: Dict[str, Any] = Depends(get_admin_user)):
    DBService.delete_pain_report(pain_id)
    DBService.log_activity(admin["UserID"], f"Administrator deleted reported pain log ID {pain_id}")
    return {"success": True}

@app.delete("/api/admin/ai-recommendations/{rec_id}")
async def admin_delete_recommendation(rec_id: int, admin: Dict[str, Any] = Depends(get_admin_user)):
    DBService.delete_recommendation(rec_id)
    DBService.log_activity(admin["UserID"], f"Administrator deleted recommendation record ID {rec_id}")
    return {"success": True}

@app.post("/api/admin/announcements", status_code=201)
async def admin_publish_announcement(req: AnnouncementRequest, admin: Dict[str, Any] = Depends(get_admin_user)):
    DBService.create_notification(
        user_id=None, # Universal announcement
        title=f"Admin Announcement: {req.title}",
        message=req.message,
        is_announcement=True
    )
    DBService.log_activity(admin["UserID"], f"Administrator published announcement: {req.title}")
    return {"success": True, "message": "Announcement published successfully to all users."}
