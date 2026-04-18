using ELearnAPI.Data;
using ELearnAPI.Models;
using Microsoft.EntityFrameworkCore;

namespace ELearnAPI.Repositories;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(int id);
    Task<User?> GetByEmailAsync(string email);
    Task<User> CreateAsync(User user);
    Task<User?> UpdateAsync(int id, User updated);
}

public interface ICourseRepository
{
    Task<IEnumerable<Course>> GetAllAsync();
    Task<Course?> GetByIdAsync(int id);
    Task<Course> CreateAsync(Course course);
    Task<Course?> UpdateAsync(int id, Course updated);
    Task<bool> DeleteAsync(int id);
}

public interface ILessonRepository
{
    Task<IEnumerable<Lesson>> GetByCourseAsync(int courseId);
    Task<Lesson> CreateAsync(Lesson lesson);
    Task<Lesson?> UpdateAsync(int id, Lesson updated);
    Task<bool> DeleteAsync(int id);
}

public interface IQuizRepository
{
    Task<IEnumerable<Quiz>> GetByCourseAsync(int courseId);
    Task<Quiz?> GetByIdWithQuestionsAsync(int quizId);
    Task<Quiz> CreateAsync(Quiz quiz);
}

public interface IQuestionRepository
{
    Task<Question> CreateAsync(Question question);
    Task<IEnumerable<Question>> GetByQuizAsync(int quizId);
}

public interface IResultRepository
{
    Task<Result> CreateAsync(Result result);
    Task<IEnumerable<Result>> GetByUserAsync(int userId);
    Task<double> GetAverageScoreAsync();
    Task<IEnumerable<Result>> GetAboveAverageAsync();
}

// ── Implementations ──

public class UserRepository(AppDbContext db) : IUserRepository
{
    public Task<User?> GetByIdAsync(int id) =>
        db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.UserId == id);

    public Task<User?> GetByEmailAsync(string email) =>
        db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Email == email);

    public async Task<User> CreateAsync(User user)
    {
        db.Users.Add(user);
        await db.SaveChangesAsync();
        return user;
    }

    public async Task<User?> UpdateAsync(int id, User updated)
    {
        var user = await db.Users.FindAsync(id);
        if (user is null) return null;
        user.FullName = updated.FullName;
        user.Email = updated.Email;
        user.Bio = updated.Bio;
        await db.SaveChangesAsync();
        return user;
    }
}

public class CourseRepository(AppDbContext db) : ICourseRepository
{
    public async Task<IEnumerable<Course>> GetAllAsync() =>
        await db.Courses.AsNoTracking()
            .Include(c => c.Lessons)
            .Include(c => c.Quizzes)
            .OrderBy(c => c.CreatedAt)
            .ToListAsync();

    public Task<Course?> GetByIdAsync(int id) =>
        db.Courses.AsNoTracking()
            .Include(c => c.Lessons)
            .Include(c => c.Quizzes)
            .FirstOrDefaultAsync(c => c.CourseId == id);

    public async Task<Course> CreateAsync(Course course)
    {
        db.Courses.Add(course);
        await db.SaveChangesAsync();
        return course;
    }

    public async Task<Course?> UpdateAsync(int id, Course updated)
    {
        var course = await db.Courses.FindAsync(id);
        if (course is null) return null;
        course.Title = updated.Title;
        course.Description = updated.Description;
        course.Category = updated.Category;
        course.Duration = updated.Duration;
        course.Icon = updated.Icon;
        await db.SaveChangesAsync();
        return course;
    }

    public async Task<bool> DeleteAsync(int id)
    {
        var course = await db.Courses.FindAsync(id);
        if (course is null) return false;
        db.Courses.Remove(course);
        await db.SaveChangesAsync();
        return true;
    }
}

public class LessonRepository(AppDbContext db) : ILessonRepository
{
    public async Task<IEnumerable<Lesson>> GetByCourseAsync(int courseId) =>
        await db.Lessons.AsNoTracking()
            .Where(l => l.CourseId == courseId)
            .OrderBy(l => l.OrderIndex)
            .ToListAsync();

    public async Task<Lesson> CreateAsync(Lesson lesson)
    {
        db.Lessons.Add(lesson);
        await db.SaveChangesAsync();
        return lesson;
    }

    public async Task<Lesson?> UpdateAsync(int id, Lesson updated)
    {
        var lesson = await db.Lessons.FindAsync(id);
        if (lesson is null) return null;
        lesson.Title = updated.Title;
        lesson.Content = updated.Content;
        lesson.OrderIndex = updated.OrderIndex;
        await db.SaveChangesAsync();
        return lesson;
    }

    public async Task<bool> DeleteAsync(int id)
    {
        var lesson = await db.Lessons.FindAsync(id);
        if (lesson is null) return false;
        db.Lessons.Remove(lesson);
        await db.SaveChangesAsync();
        return true;
    }
}

public class QuizRepository(AppDbContext db) : IQuizRepository
{
    public async Task<IEnumerable<Quiz>> GetByCourseAsync(int courseId) =>
        await db.Quizzes.AsNoTracking()
            .Include(q => q.Questions)
            .Where(q => q.CourseId == courseId)
            .ToListAsync();

    public Task<Quiz?> GetByIdWithQuestionsAsync(int quizId) =>
        db.Quizzes.AsNoTracking()
            .Include(q => q.Questions)
            .FirstOrDefaultAsync(q => q.QuizId == quizId);

    public async Task<Quiz> CreateAsync(Quiz quiz)
    {
        db.Quizzes.Add(quiz);
        await db.SaveChangesAsync();
        return quiz;
    }
}

public class QuestionRepository(AppDbContext db) : IQuestionRepository
{
    public async Task<Question> CreateAsync(Question question)
    {
        db.Questions.Add(question);
        await db.SaveChangesAsync();
        return question;
    }

    public async Task<IEnumerable<Question>> GetByQuizAsync(int quizId) =>
        await db.Questions.AsNoTracking()
            .Where(q => q.QuizId == quizId)
            .ToListAsync();
}

public class ResultRepository(AppDbContext db) : IResultRepository
{
    public async Task<Result> CreateAsync(Result result)
    {
        db.Results.Add(result);
        await db.SaveChangesAsync();
        return result;
    }

    public async Task<IEnumerable<Result>> GetByUserAsync(int userId) =>
        await db.Results.AsNoTracking()
            .Include(r => r.User)
            .Include(r => r.Quiz)
            .Where(r => r.UserId == userId)
            .OrderByDescending(r => r.AttemptDate)
            .ToListAsync();

    public async Task<double> GetAverageScoreAsync() =>
        await db.Results.AnyAsync()
            ? await db.Results.AverageAsync(r => (double)r.Score / r.TotalQuestions * 100)
            : 0;

    public async Task<IEnumerable<Result>> GetAboveAverageAsync()
    {
        var avg = await GetAverageScoreAsync();
        return await db.Results.AsNoTracking()
            .Include(r => r.User)
            .Include(r => r.Quiz)
            .Where(r => (double)r.Score / r.TotalQuestions * 100 > avg)
            .ToListAsync();
    }
}
