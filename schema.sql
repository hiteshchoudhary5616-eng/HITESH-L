-- SQL Schema for AI Injury Prevention Assistant
-- Compatible with MySQL (XAMPP / phpMyAdmin / Cloud SQL)

CREATE DATABASE IF NOT EXISTS injury_prevention_db;
USE injury_prevention_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Role ENUM('user','admin') DEFAULT 'user',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Fitness Profile Table
CREATE TABLE IF NOT EXISTS FitnessProfile (
    ProfileID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Age INT,
    Gender VARCHAR(20),
    Height DECIMAL(5,2), -- in cm
    Weight DECIMAL(5,2), -- in kg
    BMI DECIMAL(5,2),
    Experience ENUM('Beginner','Intermediate','Advanced'),
    Goal VARCHAR(50),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 3. Exercises Table
CREATE TABLE IF NOT EXISTS Exercises (
    ExerciseID INT AUTO_INCREMENT PRIMARY KEY,
    ExerciseName VARCHAR(100) NOT NULL,
    MuscleGroup VARCHAR(50) NOT NULL,
    Description TEXT,
    SafetyTips TEXT,
    Difficulty VARCHAR(20),
    Equipment VARCHAR(100)
);

-- 4. Exercise Alternatives Table
CREATE TABLE IF NOT EXISTS ExerciseAlternatives (
    AlternativeID INT AUTO_INCREMENT PRIMARY KEY,
    ExerciseID INT NOT NULL,
    AlternativeExercise VARCHAR(100) NOT NULL,
    FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID) ON DELETE CASCADE
);

-- 5. Workout History Table
CREATE TABLE IF NOT EXISTS WorkoutHistory (
    WorkoutID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Exercise VARCHAR(100) NOT NULL,
    MuscleGroup VARCHAR(50),
    Weight DECIMAL(6,2),
    Sets INT,
    Reps INT,
    Duration INT, -- in minutes
    Difficulty VARCHAR(20),
    WorkoutDate DATE NOT NULL,
    Notes TEXT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 6. Pain Reports Table
CREATE TABLE IF NOT EXISTS PainReports (
    PainID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    BodyPart VARCHAR(50) NOT NULL,
    Exercise VARCHAR(100),
    PainLevel INT NOT NULL, -- 1 to 10
    PainType VARCHAR(30), -- Sharp, Dull, Burning, Stiffness, etc.
    Duration VARCHAR(50),
    Notes TEXT,
    ReportDate DATE NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 7. AI Recommendations Table
CREATE TABLE IF NOT EXISTS AIRecommendations (
    RecommendationID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    PainID INT,
    Recommendation TEXT NOT NULL,
    RiskLevel VARCHAR(20),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (PainID) REFERENCES PainReports(PainID) ON DELETE SET NULL
);

-- 8. Recovery Plans Table
CREATE TABLE IF NOT EXISTS RecoveryPlans (
    RecoveryID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Advice TEXT,
    RecoveryDays INT,
    Status VARCHAR(20),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 9. Chat History Table
CREATE TABLE IF NOT EXISTS ChatHistory (
    ChatID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Question TEXT NOT NULL,
    Response TEXT NOT NULL,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 10. Notifications Table
CREATE TABLE IF NOT EXISTS Notifications (
    NotificationID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    Title VARCHAR(150) NOT NULL,
    Message TEXT NOT NULL,
    Status ENUM('unread','read') DEFAULT 'unread',
    IsAnnouncement BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 11. Admin Table
CREATE TABLE IF NOT EXISTS Admin (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Email VARCHAR(150) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL
);

-- 12. Password Reset OTP Table
CREATE TABLE IF NOT EXISTS PasswordReset (
    ResetID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    OTP VARCHAR(10) NOT NULL,
    Expiry TIMESTAMP NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- 13. Activity Log Table
CREATE TABLE IF NOT EXISTS ActivityLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    Activity VARCHAR(255),
    Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE SET NULL
);

-- ==========================================
-- SEED INITIAL DATA
-- ==========================================

-- Seed Admin
-- Email: admin@demo.com, Password: hashed password for 'admin123'
INSERT INTO Users (Name, Email, Password, Role) VALUES 
('System Admin', 'admin@demo.com', '$2a$10$A51uUfe2UvQ6k5tI8DkWb.vH7j3tPqA1X/Ksmh2OqC4V5nsh2X/42', 'admin');

-- Seed Standard User
-- Email: demo@user.com, Password: hashed password for 'demo123'
INSERT INTO Users (Name, Email, Password, Role) VALUES 
('John Doe', 'demo@user.com', '$2a$10$T8Z.X6k2gBfN1e7zW5N1Ee9rR8.b4KxL3tG4dG5nsh5N5W/9qg5G2', 'user');

-- Seed Fitness Profile for Demo User
INSERT INTO FitnessProfile (UserID, Age, Gender, Height, Weight, BMI, Experience, Goal) VALUES 
(2, 28, 'Male', 180.00, 82.00, 25.31, 'Intermediate', 'Muscle Gain');

-- Seed Exercises
INSERT INTO Exercises (ExerciseID, ExerciseName, MuscleGroup, Description, SafetyTips, Difficulty, Equipment) VALUES
(1, 'Bench Press', 'Chest', 'A classic upper body compound exercise targeting the pectoral muscles, anterior deltoids, and triceps.', 'Keep your feet flat on the floor, maintain a slight arch in your lower back, and do not flare your elbows excessively (aim for 45 degrees).', 'Intermediate', 'Barbell, Bench'),
(2, 'Push-ups', 'Chest', 'A versatile bodyweight movement that strengthens the chest, shoulders, and triceps while training core stability.', 'Maintain a rigid plank position. Do not sag your hips or crane your neck forward.', 'Beginner', 'Bodyweight'),
(3, 'Pull-ups', 'Back', 'An advanced upper body pulling exercise focusing on the latissimus dorsi, biceps, and upper back.', 'Pull with your elbows, keep your shoulders depressed and retracted at the start, and control the eccentric (lowering) phase.', 'Advanced', 'Pull-up Bar'),
(4, 'Barbell Row', 'Back', 'A powerful back exercise targeting the lats, rhomboids, traps, and rear delts, while requiring lower back stability.', 'Keep a flat back, bend at the hips, and pull the bar to your lower rib cage. Avoid rounding your spine.', 'Intermediate', 'Barbell'),
(5, 'Overhead Shoulder Press', 'Shoulders', 'A fundamental vertical pushing movement that builds shoulder strength and stability.', 'Keep your core engaged, glutes tight, and press in a straight line up. Avoid hyperextending your lower back.', 'Intermediate', 'Barbell or Dumbbells'),
(6, 'Lateral Raises', 'Shoulders', 'An isolation exercise targeting the lateral head of the deltoids to create shoulder width.', 'Lead with your elbows and maintain a slight forward bend in your torso. Do not swing the weights.', 'Beginner', 'Dumbbells'),
(7, 'Barbell Back Squat', 'Legs', 'The king of lower body compound exercises, targeting the quadriceps, glutes, hamstrings, and lower back.', 'Keep your heels flat, chest up, and push your knees outward. Descend until your thighs are parallel to the floor or lower.', 'Intermediate', 'Barbell, Squat Rack'),
(8, 'Romanian Deadlift', 'Legs', 'An excellent hinge pattern exercise targeting the hamstrings, glutes, and posterior chain.', 'Hinge at your hips, keep the weight close to your legs, and keep a flat spine. Stop when you feel a maximum stretch in hamstrings.', 'Intermediate', 'Barbell or Dumbbells'),
(9, 'Bicep Curl', 'Arms', 'An isolation exercise focusing strictly on the biceps brachii.', 'Keep your elbows pinned to your sides. Avoid swinging your body to lift the weight.', 'Beginner', 'Dumbbells or Barbell'),
(10, 'Tricep Overhead Extension', 'Arms', 'An exercise targeting the long head of the triceps by placing them in a deep stretch.', 'Keep your upper arms vertical and close to your ears. Avoid flaring your elbows outward.', 'Beginner', 'Dumbbell'),
(11, 'Plank', 'Core', 'An isometric core strength exercise that tests abdominal endurance and full-body rigidity.', 'Squeeze your glutes and core, keep a straight line from your head to your heels, and do not let your lower back sag.', 'Beginner', 'Bodyweight');

-- Seed Exercise Alternatives
INSERT INTO ExerciseAlternatives (ExerciseID, AlternativeExercise) VALUES
(1, 'Dumbbell Floor Press (Safer for shoulders)'),
(1, 'Incline Dumbbell Press (Reduces flat bench shoulder strain)'),
(3, 'Lat Pulldown (Controls weight, easier to scale)'),
(4, 'Chest-Supported Row (Eliminates lower back load)'),
(5, 'Landmine Press (Safer arc-like vertical press)'),
(7, 'Goblet Squat (Reduces spinal loading)'),
(7, 'Leg Press (Safer alternative for lower back issues)'),
(8, 'Leg Curls (Saves lower back while isolating hamstrings)');

-- Seed Workout History for Demo User (Realistic history over the last couple weeks)
INSERT INTO WorkoutHistory (UserID, Exercise, MuscleGroup, Weight, Sets, Reps, Duration, Difficulty, WorkoutDate, Notes) VALUES
(2, 'Bench Press', 'Chest', 80.00, 4, 8, 45, 'Hard', DATE_SUB(CURRENT_DATE, INTERVAL 10 DAY), 'Felt slight tightness in my right shoulder on the last set.'),
(2, 'Pull-ups', 'Back', 0.00, 3, 10, 30, 'Medium', DATE_SUB(CURRENT_DATE, INTERVAL 9 DAY), 'Lats felt great. Controlled descent.'),
(2, 'Barbell Back Squat', 'Legs', 100.00, 4, 6, 50, 'Hard', DATE_SUB(CURRENT_DATE, INTERVAL 8 DAY), 'Legs were fatigued but form felt solid.'),
(2, 'Overhead Shoulder Press', 'Shoulders', 50.00, 3, 8, 40, 'Hard', DATE_SUB(CURRENT_DATE, INTERVAL 6 DAY), 'Right shoulder felt some pinching when pressing lockout.'),
(2, 'Bench Press', 'Chest', 85.00, 3, 6, 45, 'Very Hard', DATE_SUB(CURRENT_DATE, INTERVAL 4 DAY), 'Shoulder pain became prominent on set 3. Had to stop.'),
(2, 'Bicep Curl', 'Arms', 15.00, 3, 12, 20, 'Medium', DATE_SUB(CURRENT_DATE, INTERVAL 2 DAY), 'Arm accessory day. Quick pump.');

-- Seed Pain Reports for Demo User
INSERT INTO PainReports (UserID, BodyPart, Exercise, PainLevel, PainType, Duration, Notes, ReportDate) VALUES
(2, 'Shoulder', 'Bench Press', 6, 'Sharp pinching', '3 days', 'Pinched feeling in front of right shoulder at the bottom of the bench press. Stiff the next morning.', DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY));

-- Seed AI Recommendations for Demo User
INSERT INTO AIRecommendations (UserID, PainID, Recommendation, RiskLevel, CreatedAt) VALUES
(2, 1, 'Based on your report of sharp pinching in your Shoulder during Bench Press, you may be experiencing rotator cuff impingement. This is common when elbows flare too wide or when chest pressing volume is high compared to back pulling volume.\n\nRecommendations:\n1. Temporarily replace flat Bench Press with **Dumbbell Floor Press** or **Incline Dumbbell Press** which limits shoulder extension.\n2. Add extra warm-up sets, focusing on face pulls and band pull-aparts.\n3. Keep your chest pressing volume down and double your back pulling volume for structural balance.\n4. Avoid lifting through sharp pain.', 'Medium', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 3 DAY));
