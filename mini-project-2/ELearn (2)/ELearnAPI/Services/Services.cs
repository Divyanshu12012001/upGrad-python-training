using AutoMapper;
using ELearnAPI.DTOs;
using ELearnAPI.Models;
using ELearnAPI.Repositories;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;

namespace ELearnAPI.Services;

public interface IUserService
{
    Task<UserDto?> RegisterAsync(RegisterDto dto);
    Task<LoginResponseDto?> LoginAsync(LoginDto dto);
    Task<UserDto?> GetByIdAsync(int id);
    Task<UserDto?> UpdateAsync(int id, UpdateUserDto dto);
}

public interface ICourseService
{
    Task<IEnumerable<CourseDto>> GetAllAsync();
    Task<CourseDto?> GetByIdAsync(int id);
    Task<CourseDto> CreateAsync(CreateCourseDto dto);
    Task<CourseDto?> UpdateAsync(int id, UpdateCourseDto dto);
    Task<bool> DeleteAsync(int id);
}

public interface ILessonService
{
    Task<IEnumerable<LessonDto>> GetByCourseAsync(int courseId);
    Task<LessonDto> CreateAsync(CreateLessonDto dto);
    Task<LessonDto?> UpdateAsync(int id, UpdateLessonDto dto);
    Task<bool> DeleteAsync(int id);
}

public interface IQuizService
{
    Task<IEnumerable<QuizDto>> GetByCourseAsync(int courseId);
    Task<IEnumerable<QuestionDto>> GetQuestionsAsync(int quizId);
    Task<QuizDto> CreateAsync(CreateQuizDto dto);
    Task<QuestionDto> AddQuestionAsync(CreateQuestionDto dto);
    Task<QuizResultDto?> SubmitAsync(int quizId, QuizSubmitDto dto);
}

public interface IResultService
{
    Task<IEnumerable<ResultDto>> GetByUserAsync(int userId);
    Task<IEnumerable<ResultDto>> GetAboveAverageAsync();
}

// ── Implementations ──

public class UserService(IUserRepository repo, IMapper mapper, IConfiguration config) : IUserService
{
    public async Task<UserDto?> RegisterAsync(RegisterDto dto)
    {
        if (await repo.GetByEmailAsync(dto.Email) is not null) return null;
        var user = new User
        {
            FullName = dto.FullName,
            Email = dto.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password)
        };
        var created = await repo.CreateAsync(user);
        return mapper.Map<UserDto>(created);
    }

    public async Task<LoginResponseDto?> LoginAsync(LoginDto dto)
    {
        var user = await repo.GetByEmailAsync(dto.Email);
        if (user is null || !BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash)) return null;
        return new LoginResponseDto
        {
            UserId = user.UserId,
            FullName = user.FullName,
            Email = user.Email,
            Token = GenerateToken(user)
        };
    }

    public async Task<UserDto?> GetByIdAsync(int id)
    {
        var user = await repo.GetByIdAsync(id);
        return user is null ? null : mapper.Map<UserDto>(user);
    }

    public async Task<UserDto?> UpdateAsync(int id, UpdateUserDto dto)
    {
        var updated = await repo.UpdateAsync(id, new User { FullName = dto.FullName, Email = dto.Email, Bio = dto.Bio });
        return updated is null ? null : mapper.Map<UserDto>(updated);
    }

    private string GenerateToken(User user)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(
            config["Jwt:Key"] ?? "ELearnDefaultSecretKey_ChangeInProduction_32chars!"));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.UserId.ToString()),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Name, user.FullName)
        };
        var token = new JwtSecurityToken(
            issuer: config["Jwt:Issuer"] ?? "ELearnAPI",
            audience: config["Jwt:Audience"] ?? "ELearnFrontend",
            claims: claims,
            expires: DateTime.UtcNow.AddDays(7),
            signingCredentials: creds);
        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}

public class CourseService(ICourseRepository repo, IMapper mapper) : ICourseService
{
    public async Task<IEnumerable<CourseDto>> GetAllAsync() =>
        mapper.Map<IEnumerable<CourseDto>>(await repo.GetAllAsync());

    public async Task<CourseDto?> GetByIdAsync(int id)
    {
        var course = await repo.GetByIdAsync(id);
        return course is null ? null : mapper.Map<CourseDto>(course);
    }

    public async Task<CourseDto> CreateAsync(CreateCourseDto dto)
    {
        var course = mapper.Map<Course>(dto);
        return mapper.Map<CourseDto>(await repo.CreateAsync(course));
    }

    public async Task<CourseDto?> UpdateAsync(int id, UpdateCourseDto dto)
    {
        var updated = await repo.UpdateAsync(id, mapper.Map<Course>(dto));
        return updated is null ? null : mapper.Map<CourseDto>(updated);
    }

    public Task<bool> DeleteAsync(int id) => repo.DeleteAsync(id);
}

public class LessonService(ILessonRepository repo, IMapper mapper) : ILessonService
{
    public async Task<IEnumerable<LessonDto>> GetByCourseAsync(int courseId) =>
        mapper.Map<IEnumerable<LessonDto>>(await repo.GetByCourseAsync(courseId));

    public async Task<LessonDto> CreateAsync(CreateLessonDto dto) =>
        mapper.Map<LessonDto>(await repo.CreateAsync(mapper.Map<Lesson>(dto)));

    public async Task<LessonDto?> UpdateAsync(int id, UpdateLessonDto dto)
    {
        var updated = await repo.UpdateAsync(id, mapper.Map<Lesson>(dto));
        return updated is null ? null : mapper.Map<LessonDto>(updated);
    }

    public Task<bool> DeleteAsync(int id) => repo.DeleteAsync(id);
}

public class QuizService(IQuizRepository quizRepo, IQuestionRepository questionRepo,
    IResultRepository resultRepo, IMapper mapper) : IQuizService
{
    public async Task<IEnumerable<QuizDto>> GetByCourseAsync(int courseId) =>
        mapper.Map<IEnumerable<QuizDto>>(await quizRepo.GetByCourseAsync(courseId));

    public async Task<IEnumerable<QuestionDto>> GetQuestionsAsync(int quizId)
    {
        var quiz = await quizRepo.GetByIdWithQuestionsAsync(quizId);
        return quiz is null ? [] : mapper.Map<IEnumerable<QuestionDto>>(quiz.Questions);
    }

    public async Task<QuizDto> CreateAsync(CreateQuizDto dto) =>
        mapper.Map<QuizDto>(await quizRepo.CreateAsync(mapper.Map<Quiz>(dto)));

    public async Task<QuestionDto> AddQuestionAsync(CreateQuestionDto dto) =>
        mapper.Map<QuestionDto>(await questionRepo.CreateAsync(mapper.Map<Question>(dto)));

    public async Task<QuizResultDto?> SubmitAsync(int quizId, QuizSubmitDto dto)
    {
        var quiz = await quizRepo.GetByIdWithQuestionsAsync(quizId);
        if (quiz is null) return null;

        var score = quiz.Questions.Count(q =>
            dto.Answers.Any(a => a.QuestionId == q.QuestionId &&
                a.SelectedAnswer.Equals(q.CorrectAnswer, StringComparison.OrdinalIgnoreCase)));

        var result = await resultRepo.CreateAsync(new Result
        {
            UserId = dto.UserId,
            QuizId = quizId,
            Score = score,
            TotalQuestions = quiz.Questions.Count
        });

        var pct = result.TotalQuestions == 0 ? 0
            : (int)Math.Round((double)result.Score / result.TotalQuestions * 100);

        return new QuizResultDto
        {
            ResultId = result.ResultId,
            UserId = result.UserId,
            QuizId = result.QuizId,
            Score = result.Score,
            TotalQuestions = result.TotalQuestions,
            Percentage = pct,
            Grade = CalcGrade(pct),
            Passed = pct >= 50,
            AttemptDate = result.AttemptDate
        };
    }

    private static string CalcGrade(int pct) => pct switch
    {
        >= 90 => "A+", >= 80 => "A", >= 70 => "B", >= 60 => "C", >= 50 => "D", _ => "F"
    };
}

public class ResultService(IResultRepository repo, IMapper mapper) : IResultService
{
    public async Task<IEnumerable<ResultDto>> GetByUserAsync(int userId) =>
        mapper.Map<IEnumerable<ResultDto>>(await repo.GetByUserAsync(userId));

    public async Task<IEnumerable<ResultDto>> GetAboveAverageAsync() =>
        mapper.Map<IEnumerable<ResultDto>>(await repo.GetAboveAverageAsync());
}
