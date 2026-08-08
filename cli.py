import os
import sys
import json
import asyncio

# Adjust Python path to include parent directory if running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python_backend.db import DBService, db
from python_backend.risk_engine import calculate_injury_risk
from python_backend.ai_service import generate_fallback_analysis, generate_analysis

async def run_cli_diagnostic():
    print("=" * 60)
    print("   AI Injury Prevention Assistant - CLI Diagnostic Tool")
    print("=" * 60)
    
    # Initialize the Database
    DBService.ensure_ready()
    
    # Let's diagnostic Demo User (ID: 2 - John Doe)
    user_id = 2
    user = DBService.get_user_by_id(user_id)
    if not user:
        print("Demo User (John Doe) not found. Database seeding error.")
        return
        
    print(f"Athlete profile loaded: {user['Name']} ({user['Email']})")
    
    profile = DBService.get_profile_by_user_id(user_id)
    if profile:
        print(f"  • Age: {profile['Age']}, Goal: {profile['Goal']}, Experience: {profile['Experience']}")
        print(f"  • Physical Stats: {profile['Height']}cm, {profile['Weight']}kg (BMI: {profile['BMI']})")
    else:
        print("  • No active fitness profile.")
        
    workouts = DBService.get_workouts_by_user_id(user_id)
    print(f"  • Logged Workouts count: {len(workouts)}")
    for w in workouts[:3]:
        print(f"    - [{w['WorkoutDate']}] {w['Exercise']} ({w['Sets']}x{w['Reps']} @ {w['Weight']}kg) - Difficulty: {w['Difficulty']}")
        
    pain_reports = DBService.get_pain_reports_by_user_id(user_id)
    print(f"  • Logged Pain Reports count: {len(pain_reports)}")
    for p in pain_reports[:2]:
        print(f"    - [{p['ReportDate']}] Joint/Muscle: {p['BodyPart']}, Pain Level: {p['PainLevel']}/10 ({p['PainType']})")

    # Run Injury Risk Calculation
    print("\n" + "-" * 50)
    print("Running Injury Risk Analysis Calculation Engine...")
    print("-" * 50)
    
    assessment = calculate_injury_risk(workouts, pain_reports, profile)
    print(f"Calculated Score: {assessment['score']}/30")
    print(f"Risk Category:    {assessment['level']}")
    print("Key Contributing Risk Factors:")
    for index, f in enumerate(assessment['factors'], 1):
        print(f"  {index}. {f['factor']} (Contribution Score: {f['scoreContribution']})")

    # Run Biomechanical Analysis (tries Gemini, falls back to structural rules)
    print("\n" + "-" * 50)
    print("Executing Sports Medicine Biomechanical Advisory...")
    print("-" * 50)
    
    # This runs the async analysis function
    analysis = await generate_analysis(profile, workouts, pain_reports)
    
    print(f"Analyzed Risk Level: {analysis['riskLevel']}")
    print(f"\nBiomechanical Explanation:\n{analysis['riskExplanation']}")
    
    print("\nPossible Causes:")
    for idx, c in enumerate(analysis.get('causes', []), 1):
        print(f"  {idx}. {c}")
        
    print("\nRecommended Training Modifications:")
    for idx, r in enumerate(analysis.get('recommendations', []), 1):
        print(f"  {idx}. {r}")
        
    print("\nJoint-Specific Rehab & Mobility Exercises:")
    for idx, ra in enumerate(analysis.get('recoveryAdvice', []), 1):
        print(f"  {idx}. {ra}")
        
    print("\nBiomechanical Safe Alternative Movements:")
    for idx, sa in enumerate(analysis.get('saferAlternatives', []), 1):
        print(f"  {idx}. {sa}")
        
    print("\n" + "=" * 60)
    print("Diagnostics complete.")

if __name__ == "__main__":
    asyncio.run(run_cli_diagnostic())
