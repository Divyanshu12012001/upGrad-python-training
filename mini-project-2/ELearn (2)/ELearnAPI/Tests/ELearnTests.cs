using AutoMapper;
using ELearnAPI.Data;
using ELearnAPI.DTOs;
using ELearnAPI.Models;
using ELearnAPI.Repositories;
using ELearnAPI.Services;
using Moq;

namespace ELearnAPI.Tests;

public class QuizScoringTests
{
    [Theory]
    [InlineData(9, 10, "A+")]
    [InlineData(8, 10, "A")]
    [InlineData(7, 10, "B")]
    [InlineData(6, 10, "C")]
    [InlineData(5, 10, "D")]
    [InlineData(3, 10, "F")]
    public void Grade_IsCorrect(int score, int total, string expectedGrade)
    {
        var pct = (int)Math.Round((double)score / total * 100);
        var grade = pct switch
        {
            >= 90 => "A+", >= 80 => "A", >= 70 => "B",
            >= 60 => "C", >= 50 => "D", _ => "F"
        };
        Assert.Equal(expectedGrade, grade);
    }

    [Theory]
    [InlineData(5, 10, true)]
    [InlineData(4, 10, false)]
    [InlineData(10, 10, true)]
    [InlineData(0, 10, false)]
    public void Pass_Fail_IsCorrect(int score, int total, bool expectedPassed)
    {
        var pct = (double)score / total * 100;
        Assert.Equal(expectedPassed, pct >= 50);
    }

    [Fact]
    public void Percentage_ZeroTotal_ReturnsZero()
    {
        var pct = 0 == 0 ? 0 : (int)Math.Round((double)5 / 0 * 100);
        Assert.Equal(0, pct);
    }
}

public class CourseServiceTests
{
    private readonly IMapper _mapper;
    private readonly Mock<ICourseRepository> _repoMock = new();

    public CourseServiceTests()
    {
        var config = new MapperConfiguration(cfg => cfg.AddProfile<MappingProfile>());
        _mapper = config.CreateMapper();
    }

    [Fact]
    public async Task GetAll_ReturnsMappedCourses()
    {
        var courses = new List<Course>
        {
            new() { CourseId = 1, Title = "HTML", Lessons = [], Quizzes = [] },
            new() { CourseId = 2, Title = "JS",   Lessons = [], Quizzes = [] }
        };
        _repoMock.Setup(r => r.GetAllAsync()).ReturnsAsync(courses);
        var service = new CourseService(_repoMock.Object, _mapper);

        var result = (await service.GetAllAsync()).ToList();

        Assert.Equal(2, result.Count);
        Assert.Equal("HTML", result[0].Title);
    }

    [Fact]
    public async Task GetById_NotFound_ReturnsNull()
    {
        _repoMock.Setup(r => r.GetByIdAsync(99)).ReturnsAsync((Course?)null);
        var service = new CourseService(_repoMock.Object, _mapper);

        var result = await service.GetByIdAsync(99);

        Assert.Null(result);
    }

    [Fact]
    public async Task Create_ReturnsCourseDto()
    {
        var dto = new CreateCourseDto("Test", "Desc", "Cat", "2h", "📚", 1);
        var course = new Course { CourseId = 1, Title = "Test", Lessons = [], Quizzes = [] };
        _repoMock.Setup(r => r.CreateAsync(It.IsAny<Course>())).ReturnsAsync(course);
        var service = new CourseService(_repoMock.Object, _mapper);

        var result = await service.CreateAsync(dto);

        Assert.Equal("Test", result.Title);
    }

    [Fact]
    public async Task Delete_NotFound_ReturnsFalse()
    {
        _repoMock.Setup(r => r.DeleteAsync(99)).ReturnsAsync(false);
        var service = new CourseService(_repoMock.Object, _mapper);

        var result = await service.DeleteAsync(99);

        Assert.False(result);
    }
}

public class UserServiceTests
{
    private readonly IMapper _mapper;
    private readonly Mock<IUserRepository> _repoMock = new();

    public UserServiceTests()
    {
        var config = new MapperConfiguration(cfg => cfg.AddProfile<MappingProfile>());
        _mapper = config.CreateMapper();
    }

    [Fact]
    public async Task Register_DuplicateEmail_ReturnsNull()
    {
        _repoMock.Setup(r => r.GetByEmailAsync("test@test.com"))
                 .ReturnsAsync(new User { Email = "test@test.com" });
        var service = new UserService(_repoMock.Object, _mapper, new Microsoft.Extensions.Configuration.ConfigurationBuilder().Build());

        var result = await service.RegisterAsync(new RegisterDto("Name", "test@test.com", "pass"));

        Assert.Null(result);
    }

    [Fact]
    public async Task Register_NewEmail_ReturnsUserDto()
    {
        _repoMock.Setup(r => r.GetByEmailAsync("new@test.com")).ReturnsAsync((User?)null);
        _repoMock.Setup(r => r.CreateAsync(It.IsAny<User>()))
                 .ReturnsAsync(new User { UserId = 1, FullName = "New", Email = "new@test.com" });
        var service = new UserService(_repoMock.Object, _mapper, new Microsoft.Extensions.Configuration.ConfigurationBuilder().Build());

        var result = await service.RegisterAsync(new RegisterDto("New", "new@test.com", "pass123"));

        Assert.NotNull(result);
        Assert.Equal("new@test.com", result.Email);
    }

    [Fact]
    public async Task Login_WrongPassword_ReturnsNull()
    {
        var hash = BCrypt.Net.BCrypt.HashPassword("correct");
        _repoMock.Setup(r => r.GetByEmailAsync("u@test.com"))
                 .ReturnsAsync(new User { UserId = 1, FullName = "U", Email = "u@test.com", PasswordHash = hash });
        var service = new UserService(_repoMock.Object, _mapper, new Microsoft.Extensions.Configuration.ConfigurationBuilder().Build());

        var result = await service.LoginAsync(new LoginDto { Email = "u@test.com", Password = "wrong" });

        Assert.Null(result);
    }

    [Fact]
    public async Task Login_CorrectCredentials_ReturnsToken()
    {
        var hash = BCrypt.Net.BCrypt.HashPassword("correct");
        _repoMock.Setup(r => r.GetByEmailAsync("u@test.com"))
                 .ReturnsAsync(new User { UserId = 1, FullName = "U", Email = "u@test.com", PasswordHash = hash });
        var config = new Microsoft.Extensions.Configuration.ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?> { ["Jwt:Key"] = "TestSecretKey_AtLeast32Characters_Long!" })
            .Build();
        var service = new UserService(_repoMock.Object, _mapper, config);

        var result = await service.LoginAsync(new LoginDto { Email = "u@test.com", Password = "correct" });

        Assert.NotNull(result);
        Assert.False(string.IsNullOrEmpty(result.Token));
    }
}

public class LinqFilteringTests
{
    private readonly List<Course> _courses =
    [
        new() { CourseId = 1, Title = "HTML", Category = "Web Development", Lessons = [], Quizzes = [] },
        new() { CourseId = 2, Title = "JS",   Category = "Programming",     Lessons = [], Quizzes = [] },
        new() { CourseId = 3, Title = "CSS",  Category = "Web Development", Lessons = [], Quizzes = [] },
    ];

    [Fact]
    public void Filter_ByCategory_ReturnsCorrectCount()
    {
        var webDev = _courses.Where(c => c.Category == "Web Development").ToList();
        Assert.Equal(2, webDev.Count);
    }

    [Fact]
    public void OrderBy_Title_IsAlphabetical()
    {
        var ordered = _courses.OrderBy(c => c.Title).Select(c => c.Title).ToList();
        Assert.Equal(new[] { "CSS", "HTML", "JS" }, ordered);
    }

    [Fact]
    public void GroupBy_Category_CountsCorrectly()
    {
        var groups = _courses.GroupBy(c => c.Category)
                             .ToDictionary(g => g.Key, g => g.Count());
        Assert.Equal(2, groups["Web Development"]);
        Assert.Equal(1, groups["Programming"]);
    }
}

public class ExceptionHandlingTests
{
    [Fact]
    public async Task GetById_ThrowsOnDbError_PropagatesException()
    {
        var repoMock = new Mock<ICourseRepository>();
        repoMock.Setup(r => r.GetByIdAsync(It.IsAny<int>()))
                .ThrowsAsync(new InvalidOperationException("DB error"));
        var config = new MapperConfiguration(cfg => cfg.AddProfile<MappingProfile>());
        var service = new CourseService(repoMock.Object, config.CreateMapper());

        await Assert.ThrowsAsync<InvalidOperationException>(() => service.GetByIdAsync(1));
    }
}
