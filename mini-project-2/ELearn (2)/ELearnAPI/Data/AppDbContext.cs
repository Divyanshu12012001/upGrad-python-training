using ELearnAPI.Models;
using Microsoft.EntityFrameworkCore;

namespace ELearnAPI.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Course> Courses => Set<Course>();
    public DbSet<Lesson> Lessons => Set<Lesson>();
    public DbSet<Quiz> Quizzes => Set<Quiz>();
    public DbSet<Question> Questions => Set<Question>();
    public DbSet<Result> Results => Set<Result>();

    protected override void OnModelCreating(ModelBuilder mb)
    {
        mb.Entity<User>(e => {
            e.HasKey(u => u.UserId);
            e.HasIndex(u => u.Email).IsUnique();
            e.Property(u => u.Email).HasMaxLength(200);
            e.Property(u => u.FullName).HasMaxLength(200);
            e.Property(u => u.Bio).HasMaxLength(500);
        });

        mb.Entity<Course>(e => {
            e.HasKey(c => c.CourseId);
            e.Property(c => c.Icon).HasMaxLength(20);
            e.HasOne(c => c.Creator)
             .WithMany(u => u.Courses)
             .HasForeignKey(c => c.CreatedBy)
             .OnDelete(DeleteBehavior.Restrict);
        });

        mb.Entity<Lesson>(e => {
            e.HasKey(l => l.LessonId);
            e.HasOne(l => l.Course)
             .WithMany(c => c.Lessons)
             .HasForeignKey(l => l.CourseId)
             .OnDelete(DeleteBehavior.Cascade);
        });

        mb.Entity<Quiz>(e => {
            e.HasKey(q => q.QuizId);
            e.HasOne(q => q.Course)
             .WithMany(c => c.Quizzes)
             .HasForeignKey(q => q.CourseId)
             .OnDelete(DeleteBehavior.Cascade);
        });

        mb.Entity<Question>(e => {
            e.HasKey(q => q.QuestionId);
            e.HasOne(q => q.Quiz)
             .WithMany(qz => qz.Questions)
             .HasForeignKey(q => q.QuizId)
             .OnDelete(DeleteBehavior.Cascade);
        });

        mb.Entity<Result>(e => {
            e.HasKey(r => r.ResultId);
            e.HasOne(r => r.User)
             .WithMany(u => u.Results)
             .HasForeignKey(r => r.UserId)
             .OnDelete(DeleteBehavior.Cascade);
            e.HasOne(r => r.Quiz)
             .WithMany(q => q.Results)
             .HasForeignKey(r => r.QuizId)
             .OnDelete(DeleteBehavior.Restrict);
        });
    }
}
