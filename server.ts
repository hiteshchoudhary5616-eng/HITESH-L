// Express Server Entry Point
// Implements full REST API endpoints and hosts the Vite React dev server
import express, { Request, Response, NextFunction } from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import { dbService } from './server/db.js';
import { calculateInjuryRisk } from './server/risk_engine.js';
import { generateAnalysis, chatReply } from './server/ai_service.js';
import { User } from './src/types.js';

// Load environment variables
dotenv.config();

const PORT = 3000;
const app = express();

app.use(express.json());

// Simple Auth Middleware using localStorage Bearer token (UserID) to avoid iframe cookie restrictions
interface AuthenticatedRequest extends Request {
  user?: User;
}

const authMiddleware = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Unauthorized. Missing authentication token.' });
    return;
  }
  
  const token = authHeader.split(' ')[1];
  const userId = parseInt(token, 10);
  
  if (isNaN(userId)) {
    res.status(401).json({ error: 'Invalid authentication token.' });
    return;
  }

  const user = dbService.getUserById(userId);
  if (!user) {
    res.status(401).json({ error: 'User does not exist.' });
    return;
  }

  req.user = user;
  next();
};

const adminMiddleware = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  if (!req.user || req.user.Role !== 'admin') {
    res.status(403).json({ error: 'Access denied. Administrator privileges required.' });
    return;
  }
  next();
};

// ============================================================================
// BACKEND API ENDPOINTS
// ============================================================================

// 1. Authentication Endpoints
app.post('/api/auth/register', async (req: Request, res: Response) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password) {
    res.status(400).json({ error: 'Name, email, and password are required.' });
    return;
  }

  try {
    await dbService.ensureReady();
    const existing = dbService.getUserByEmail(email);
    if (existing) {
      res.status(400).json({ error: 'A user with this email already exists.' });
      return;
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const newUser = await dbService.createUser({
      Name: name,
      Email: email,
      PasswordHash: passwordHash,
      Role: 'user'
    });

    dbService.logActivity(newUser.UserID, `User registered account`);
    
    // Seed an initial notification welcoming them
    dbService.createNotification({
      UserID: newUser.UserID,
      Title: 'Welcome aboard!',
      Message: `Hi ${name}, welcome to the AI Injury Prevention Assistant. Complete your fitness profile to get detailed biomechanical injury risk scoring!`
    });

    res.status(201).json({
      token: newUser.UserID.toString(),
      user: newUser
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to register user.' });
  }
});

app.post('/api/auth/login', async (req: Request, res: Response) => {
  const { email, password } = req.body;
  if (!email || !password) {
    res.status(400).json({ error: 'Email and password are required.' });
    return;
  }

  try {
    await dbService.ensureReady();
    const user = dbService.getUserByEmail(email);
    if (!user) {
      res.status(401).json({ error: 'Invalid email or password.' });
      return;
    }

    // Since our local seed has both admin and user, let's verify password safely.
    // In our JSON file we store password as User.Password
    const storedHash = (user as any).Password;
    const isMatch = await bcrypt.compare(password, storedHash);
    
    if (!isMatch) {
      res.status(401).json({ error: 'Invalid email or password.' });
      return;
    }

    dbService.logActivity(user.UserID, `User logged in successfully`);

    res.json({
      token: user.UserID.toString(),
      user: {
        UserID: user.UserID,
        Name: user.Name,
        Email: user.Email,
        Role: user.Role
      }
    });
  } catch (err) {
    res.status(500).json({ error: 'Server authentication failure.' });
  }
});

app.post('/api/auth/forgot-password', async (req: Request, res: Response) => {
  const { email } = req.body;
  if (!email) {
    res.status(400).json({ error: 'Email is required.' });
    return;
  }

  try {
    await dbService.ensureReady();
    const user = dbService.getUserByEmail(email);
    if (!user) {
      res.status(404).json({ error: 'No account found with this email.' });
      return;
    }

    // Generate numeric 6 digit OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    dbService.createPasswordReset(user.UserID, otp);
    dbService.logActivity(user.UserID, `Generated password reset OTP: ${otp}`);

    // As per specifications: "email" it by displaying it on-screen (mock email flow)
    res.json({ 
      message: 'Password reset code generated.',
      otp: otp // Displaying directly to client for demo purposes
    });
  } catch (err) {
    res.status(500).json({ error: 'Forgot password operation failed.' });
  }
});

app.post('/api/auth/reset-password', async (req: Request, res: Response) => {
  const { email, otp, newPassword } = req.body;
  if (!email || !otp || !newPassword) {
    res.status(400).json({ error: 'Email, OTP reset code, and new password are required.' });
    return;
  }

  try {
    await dbService.ensureReady();
    const user = dbService.getUserByEmail(email);
    if (!user) {
      res.status(404).json({ error: 'Account not found.' });
      return;
    }

    const isValid = dbService.verifyResetOTP(user.UserID, otp);
    if (!isValid) {
      res.status(400).json({ error: 'Invalid or expired OTP reset code.' });
      return;
    }

    const newHash = await bcrypt.hash(newPassword, 10);
    dbService.updateUserPassword(user.UserID, newHash);
    dbService.logActivity(user.UserID, `Password reset successfully via OTP`);

    res.json({ message: 'Password has been reset successfully.' });
  } catch (err) {
    res.status(500).json({ error: 'Reset password operation failed.' });
  }
});

app.post('/api/auth/change-password', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { currentPassword, newPassword } = req.body;
  if (!currentPassword || !newPassword) {
    res.status(400).json({ error: 'Current password and new password are required.' });
    return;
  }

  try {
    const user = req.user!;
    const storedHash = (user as any).Password;
    const isMatch = await bcrypt.compare(currentPassword, storedHash);

    if (!isMatch) {
      res.status(400).json({ error: 'Incorrect current password.' });
      return;
    }

    const newHash = await bcrypt.hash(newPassword, 10);
    dbService.updateUserPassword(user.UserID, newHash);
    dbService.logActivity(user.UserID, `User changed account password`);

    res.json({ message: 'Password updated successfully.' });
  } catch (err) {
    res.status(500).json({ error: 'Change password operation failed.' });
  }
});

// 2. Profile Endpoints
app.get('/api/profile', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const profile = dbService.getProfileByUserId(req.user!.UserID);
    res.json(profile);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load profile.' });
  }
});

app.put('/api/profile', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { age, gender, height, weight, experience, goal } = req.body;
  try {
    const updated = dbService.upsertProfile({
      UserID: req.user!.UserID,
      Age: Number(age) || 0,
      Gender: gender || 'Other',
      Height: Number(height) || 0,
      Weight: Number(weight) || 0,
      Experience: experience || 'Beginner',
      Goal: goal || 'General Fitness'
    });

    dbService.logActivity(req.user!.UserID, `Updated fitness profile (BMI: ${updated.BMI})`);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update profile.' });
  }
});

// 3. Workout Tracker Endpoints
app.get('/api/workouts', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const list = dbService.getWorkoutsByUserId(req.user!.UserID);
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch workouts.' });
  }
});

app.post('/api/workouts', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { exercise, muscleGroup, weight, sets, reps, duration, difficulty, workoutDate, notes } = req.body;
  if (!exercise || !muscleGroup) {
    res.status(400).json({ error: 'Exercise name and muscle group are required.' });
    return;
  }

  try {
    const newWorkout = dbService.createWorkout({
      UserID: req.user!.UserID,
      Exercise: exercise,
      MuscleGroup: muscleGroup,
      Weight: Number(weight) || 0,
      Sets: Number(sets) || 1,
      Reps: Number(reps) || 1,
      Duration: Number(duration) || 0,
      Difficulty: difficulty || 'Medium',
      WorkoutDate: workoutDate,
      Notes: notes || ''
    });

    dbService.logActivity(req.user!.UserID, `Logged workout: ${exercise} (${sets}x${reps})`);
    res.status(201).json(newWorkout);
  } catch (err) {
    res.status(500).json({ error: 'Failed to save workout.' });
  }
});

app.put('/api/workouts/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const workoutId = parseInt(req.params.id, 10);
  try {
    const updated = dbService.updateWorkout(workoutId, req.body);
    if (!updated) {
      res.status(404).json({ error: 'Workout not found.' });
      return;
    }
    dbService.logActivity(req.user!.UserID, `Updated workout ID ${workoutId}`);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update workout.' });
  }
});

app.delete('/api/workouts/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const workoutId = parseInt(req.params.id, 10);
  try {
    dbService.deleteWorkout(workoutId);
    dbService.logActivity(req.user!.UserID, `Deleted workout ID ${workoutId}`);
    res.json({ message: 'Workout deleted successfully.' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete workout.' });
  }
});

// 4. Pain Assessment Endpoints
app.get('/api/pain-reports', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const reports = dbService.getPainReportsByUserId(req.user!.UserID);
    res.json(reports);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load pain reports.' });
  }
});

app.post('/api/pain-reports', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { bodyPart, exercise, painLevel, painType, duration, notes, reportDate } = req.body;
  if (!bodyPart || painLevel === undefined) {
    res.status(400).json({ error: 'Affected body part and pain level are required.' });
    return;
  }

  try {
    const newReport = dbService.createPainReport({
      UserID: req.user!.UserID,
      BodyPart: bodyPart,
      Exercise: exercise || 'None',
      PainLevel: Number(painLevel) || 1,
      PainType: painType || 'Stiffness',
      Duration: duration || '1 day',
      Notes: notes || '',
      ReportDate: reportDate
    });

    dbService.logActivity(req.user!.UserID, `Logged pain report: ${bodyPart} (Level ${painLevel}/10)`);

    // High pain levels trigger safety warnings and immediate recovery notifications
    if (painLevel >= 6) {
      dbService.createNotification({
        UserID: req.user!.UserID,
        Title: `High Pain Level Warning: ${bodyPart}`,
        Message: `You reported a Level ${painLevel} pain for your ${bodyPart}. We strongly suggest running an AI Injury Risk Analysis and resting from heavy sets.`
      });
    }

    res.status(201).json(newReport);
  } catch (err) {
    res.status(500).json({ error: 'Failed to save pain report.' });
  }
});

app.put('/api/pain-reports/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const painId = parseInt(req.params.id, 10);
  try {
    const updated = dbService.updatePainReport(painId, req.body);
    if (!updated) {
      res.status(404).json({ error: 'Pain report not found.' });
      return;
    }
    dbService.logActivity(req.user!.UserID, `Updated pain report ID ${painId}`);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update pain report.' });
  }
});

app.delete('/api/pain-reports/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const painId = parseInt(req.params.id, 10);
  try {
    dbService.deletePainReport(painId);
    dbService.logActivity(req.user!.UserID, `Deleted pain report ID ${painId}`);
    res.json({ message: 'Pain report deleted successfully.' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete pain report.' });
  }
});

// 5. AI Analysis Endpoints
app.get('/api/ai/history', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    await dbService.ensureReady();
    const history = dbService.getRecommendationsByUserId(req.user!.UserID);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load analysis history.' });
  }
});

app.post('/api/ai/analyze', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    await dbService.ensureReady();
    const userId = req.user!.UserID;
    const profile = dbService.getProfileByUserId(userId);
    const workouts = dbService.getWorkoutsByUserId(userId);
    const painReports = dbService.getPainReportsByUserId(userId);

    const result = await generateAnalysis(profile, workouts, painReports);

    // Save as recommendation in DB
    const latestPain = painReports.length > 0 ? painReports[0].PainID : null;
    const savedRec = dbService.createRecommendation({
      UserID: userId,
      PainID: latestPain,
      Recommendation: JSON.stringify(result), // Store fully structured as JSON string
      RiskLevel: result.riskLevel
    });

    dbService.logActivity(userId, `Triggered AI Injury Risk Analysis (Risk: ${result.riskLevel})`);

    // Create custom notification detailing the recommendation
    dbService.createNotification({
      UserID: userId,
      Title: `AI Safety Analysis Complete`,
      Message: `Your Injury Risk is estimated as ${result.riskLevel}. Alternatives recommended: ${result.saferAlternatives.slice(0, 2).join(', ')}.`
    });

    res.json(savedRec);
  } catch (err) {
    console.error('API Analyze Error:', err);
    res.status(500).json({ error: 'AI Analysis engine failed to process logs.' });
  }
});

// 6. Exercise Library Endpoints
app.get('/api/exercises', async (req: Request, res: Response) => {
  const category = req.query.category as string;
  const search = req.query.search as string;

  try {
    await dbService.ensureReady();
    let list = dbService.getExercises();

    if (category) {
      list = list.filter(e => e.MuscleGroup.toLowerCase() === category.toLowerCase());
    }

    if (search) {
      const q = search.toLowerCase();
      list = list.filter(e => 
        e.ExerciseName.toLowerCase().includes(q) || 
        e.Description.toLowerCase().includes(q)
      );
    }

    res.json(list);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve exercise library.' });
  }
});

app.get('/api/exercises/:id', async (req: Request, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    const ex = dbService.getExerciseById(id);
    if (!ex) {
      res.status(404).json({ error: 'Exercise not found.' });
      return;
    }
    res.json(ex);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve exercise details.' });
  }
});

app.post('/api/exercises', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { exerciseName, muscleGroup, description, safetyTips, difficulty, equipment, alternatives } = req.body;
  if (!exerciseName || !muscleGroup) {
    res.status(400).json({ error: 'Exercise name and muscle group are required.' });
    return;
  }

  try {
    const newEx = dbService.createExercise({
      ExerciseName: exerciseName,
      MuscleGroup: muscleGroup,
      Description: description || 'Custom user-created workout.',
      SafetyTips: safetyTips || 'Maintain steady biomechanics and proper form.',
      Difficulty: difficulty || 'Intermediate',
      Equipment: equipment || 'None',
      Alternatives: alternatives || []
    });

    dbService.logActivity(req.user!.UserID, `User created exercise: ${exerciseName}`);
    res.status(201).json(newEx);
  } catch (err) {
    res.status(500).json({ error: 'Failed to save exercise.' });
  }
});

// 7. Injury Risk Score Endpoint
app.get('/api/risk/current', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.UserID;
    const profile = dbService.getProfileByUserId(userId);
    const workouts = dbService.getWorkoutsByUserId(userId);
    const painReports = dbService.getPainReportsByUserId(userId);

    const score = calculateInjuryRisk(workouts, painReports, profile);
    res.json(score);
  } catch (err) {
    res.status(500).json({ error: 'Failed to compute risk assessment.' });
  }
});

// 8. AI Chatbot Endpoints
app.get('/api/chat/history', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const chatHist = dbService.getChatHistoryByUserId(req.user!.UserID);
    res.json(chatHist);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load chat history.' });
  }
});

app.post('/api/chat', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { question } = req.body;
  if (!question) {
    res.status(400).json({ error: 'Question is required.' });
    return;
  }

  try {
    const userId = req.user!.UserID;
    const profile = dbService.getProfileByUserId(userId);
    const workouts = dbService.getWorkoutsByUserId(userId);
    const painReports = dbService.getPainReportsByUserId(userId);

    const answer = await chatReply(profile, workouts, painReports, question);

    const messageObj = dbService.addChatMessage(userId, question, answer);
    res.json(messageObj);
  } catch (err) {
    res.status(500).json({ error: 'Chat bot engine failed.' });
  }
});

// 9. Notifications Endpoints
app.get('/api/notifications', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const list = dbService.getNotificationsByUserId(req.user!.UserID);
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve notifications.' });
  }
});

app.patch('/api/notifications/:id/read', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    dbService.markNotificationAsRead(id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to update notification state.' });
  }
});

// 10. Unified Dashboard Payload Endpoint
app.get('/api/dashboard', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.UserID;
    await dbService.ensureReady();
    const profile = dbService.getProfileByUserId(userId);
    const workouts = dbService.getWorkoutsByUserId(userId);
    const painReports = dbService.getPainReportsByUserId(userId);
    const riskAssessment = calculateInjuryRisk(workouts, painReports, profile);
    const recentRecommendations = dbService.getRecommendationsByUserId(userId);
    const unreadNotificationsCount = dbService.getUnreadNotificationsCount(userId);

    // Rule-based: Generate safety reminders on the fly on login/dashboard fetch (Module 10)
    // 1. Overtraining check
    let consecutiveDays = 0;
    const sortedUniqueDates = [...new Set(workouts.map(w => w.WorkoutDate))].sort((a,b) => b.localeCompare(a));
    if (sortedUniqueDates.length > 0) {
      let checkDate = new Date();
      for (let i = 0; i < 7; i++) {
        const dateStr = checkDate.toISOString().split('T')[0];
        if (sortedUniqueDates.includes(dateStr)) {
          consecutiveDays++;
          checkDate.setDate(checkDate.getDate() - 1);
        } else {
          break;
        }
      }
    }
    const existingNotifs = dbService.getNotificationsByUserId(userId);
    const hasNotif = (title: string) => existingNotifs.some(n => n.Title === title);

    if (consecutiveDays >= 3 && !hasNotif('Rest Recommended Tomorrow')) {
      dbService.createNotification({
        UserID: userId,
        Title: 'Rest Recommended Tomorrow',
        Message: `You have trained for ${consecutiveDays} consecutive days. Muscle fibers rebuild during rest. Take a day off tomorrow!`
      });
    }

    // 2. High Pain recovery reminder
    if (painReports.length > 0 && painReports[0].PainLevel >= 5 && !hasNotif('Recovery Reminder: Focus on Mobility')) {
      const painAge = (Date.now() - new Date(painReports[0].ReportDate).getTime()) / (1000 * 60 * 60 * 24);
      if (painAge <= 3) {
        dbService.createNotification({
          UserID: userId,
          Title: 'Recovery Reminder: Focus on Mobility',
          Message: `You logged an active pain of ${painReports[0].PainLevel}/10 for your ${painReports[0].BodyPart} recently. Prioritize 15 minutes of dedicated dynamic stretching and mobility exercises today.`
        });
      }
    }

    // 3. No workouts logged in 3 days
    if (workouts.length > 0 && !hasNotif('Ready to stretch and sweat?')) {
      const daysSinceWorkout = (Date.now() - new Date(workouts[0].WorkoutDate).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceWorkout >= 3) {
        dbService.createNotification({
          UserID: userId,
          Title: 'Ready to stretch and sweat?',
          Message: "It has been over 3 days since your last logged workout. If you are resting injuries, focus on core or low-impact cardio!"
        });
      }
    }

    // Reconstruct Weekly Volume Chart Data (Last 7 Days)
    const weeklyVolumeData: { day: string; volume: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
      
      const dayWorkouts = workouts.filter(w => w.WorkoutDate === dateStr);
      const dayVol = dayWorkouts.reduce((sum, w) => sum + (w.Weight * w.Sets * w.Reps), 0);
      weeklyVolumeData.push({ day: `${dayName} (${d.getDate()})`, volume: dayVol });
    }

    // Muscle Distribution Data (All-time or recent distribution count)
    const muscles = ['Chest', 'Back', 'Shoulders', 'Legs', 'Arms', 'Core'];
    const muscleDistributionData = muscles.map(muscle => {
      const count = workouts.filter(w => w.MuscleGroup.toLowerCase() === muscle.toLowerCase()).length;
      return { muscle, count };
    });

    // Pain Trend Data (All pain levels chronologically over the last 14 days)
    const painTrendData = painReports
      .slice(0, 10)
      .map(p => ({
        date: p.ReportDate.split('-').slice(1).join('/'), // MM/DD format
        level: p.PainLevel
      }))
      .reverse();

    res.json({
      user: {
        UserID: req.user!.UserID,
        Name: req.user!.Name,
        Email: req.user!.Email,
        Role: req.user!.Role
      },
      profile,
      recentWorkouts: workouts.slice(0, 5),
      recentPainReports: painReports.slice(0, 5),
      riskAssessment,
      recentRecommendations: recentRecommendations.slice(0, 3),
      unreadNotificationsCount: dbService.getUnreadNotificationsCount(userId),
      weeklyVolumeData,
      muscleDistributionData,
      painTrendData
    });
  } catch (err) {
    console.error('Dashboard Endpoint Error:', err);
    res.status(500).json({ error: 'Failed to build aggregated dashboard metrics.' });
  }
});

// ============================================================================
// ADMIN ONLY BLUEPRINT ENDPOINTS
// ============================================================================

app.get('/api/admin/stats', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const stats = dbService.getAdminStats();
    const activityLogs = dbService.getActivityLogs().slice(0, 50);
    res.json({ stats, activityLogs });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch administrator statistics.' });
  }
});

app.get('/api/admin/users', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const users = dbService.getUsers().filter(u => u.Role !== 'admin');
    res.json(users);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load users.' });
  }
});

app.delete('/api/admin/users/:id', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const targetUserId = parseInt(req.params.id, 10);
  try {
    dbService.deleteUser(targetUserId);
    dbService.logActivity(req.user!.UserID, `Administrator deleted user account ID ${targetUserId}`);
    res.json({ success: true, message: 'User deleted successfully.' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete user.' });
  }
});

app.post('/api/admin/exercises', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { exerciseName, muscleGroup, description, safetyTips, difficulty, equipment, alternatives } = req.body;
  if (!exerciseName || !muscleGroup) {
    res.status(400).json({ error: 'Exercise name and muscle group are required.' });
    return;
  }

  try {
    const newEx = dbService.createExercise({
      ExerciseName: exerciseName,
      MuscleGroup: muscleGroup,
      Description: description,
      SafetyTips: safetyTips,
      Difficulty: difficulty,
      Equipment: equipment,
      Alternatives: alternatives || []
    });

    dbService.logActivity(req.user!.UserID, `Administrator created exercise: ${exerciseName}`);
    res.status(201).json(newEx);
  } catch (err) {
    res.status(500).json({ error: 'Failed to save exercise.' });
  }
});

app.put('/api/admin/exercises/:id', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    const updated = dbService.updateExercise(id, req.body);
    if (!updated) {
      res.status(404).json({ error: 'Exercise not found.' });
      return;
    }
    dbService.logActivity(req.user!.UserID, `Administrator updated exercise ID ${id}`);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update exercise.' });
  }
});

app.delete('/api/admin/exercises/:id', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    dbService.deleteExercise(id);
    dbService.logActivity(req.user!.UserID, `Administrator deleted exercise ID ${id}`);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete exercise.' });
  }
});

// Admin deletes spam pain report
app.delete('/api/admin/pain-reports/:id', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    dbService.deletePainReport(id);
    dbService.logActivity(req.user!.UserID, `Administrator deleted reported pain log ID ${id}`);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete pain report.' });
  }
});

// Admin deletes recommendation history
app.delete('/api/admin/ai-recommendations/:id', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const id = parseInt(req.params.id, 10);
  try {
    dbService.deleteRecommendation(id);
    dbService.logActivity(req.user!.UserID, `Administrator deleted recommendation record ID ${id}`);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete recommendation.' });
  }
});

// Admin posts announcement (Module 11)
app.post('/api/admin/announcements', authMiddleware, adminMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { title, message } = req.body;
  if (!title || !message) {
    res.status(400).json({ error: 'Announcement title and message are required.' });
    return;
  }

  try {
    dbService.createNotification({
      UserID: null, // Null indicates universal announcement
      Title: `Admin Announcement: ${title}`,
      Message: message,
      IsAnnouncement: true
    });

    dbService.logActivity(req.user!.UserID, `Administrator published announcement: ${title}`);
    res.status(201).json({ success: true, message: 'Announcement published successfully to all users.' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to publish announcement.' });
  }
});

// ============================================================================
// VITE CLIENT DEV MIDDLEWARE & ASSET SERVING
// ============================================================================

async function startServer() {
  await dbService.ensureReady();
  
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req: Request, res: Response) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server listening at http://0.0.0.0:${PORT}`);
  });
}

startServer();
