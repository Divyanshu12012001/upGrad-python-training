using AutoMapper;
using ELearnAPI.DTOs;
using ELearnAPI.Models;

namespace ELearnAPI.Data;

public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<User, UserDto>();
        CreateMap<UpdateUserDto, User>();

        CreateMap<Course, CourseDto>()
            .ForMember(d => d.LessonCount, o => o.MapFrom(s => s.Lessons.Count))
            .ForMember(d => d.QuizCount, o => o.MapFrom(s => s.Quizzes.Count));
        CreateMap<CreateCourseDto, Course>();
        CreateMap<UpdateCourseDto, Course>();

        CreateMap<Lesson, LessonDto>();
        CreateMap<CreateLessonDto, Lesson>();
        CreateMap<UpdateLessonDto, Lesson>();

        CreateMap<Quiz, QuizDto>()
            .ForMember(d => d.QuestionCount, o => o.MapFrom(s => s.Questions.Count));
        CreateMap<CreateQuizDto, Quiz>();

        CreateMap<Question, QuestionDto>();
        CreateMap<CreateQuestionDto, Question>();

        CreateMap<Result, ResultDto>()
            .ForMember(d => d.UserName, o => o.MapFrom(s => s.User.FullName))
            .ForMember(d => d.QuizTitle, o => o.MapFrom(s => s.Quiz.Title))
            .ForMember(d => d.Percentage, o => o.MapFrom(s =>
                s.TotalQuestions == 0 ? 0 : (int)Math.Round((double)s.Score / s.TotalQuestions * 100)))
            .ForMember(d => d.Grade, o => o.MapFrom(s => CalcGrade(
                s.TotalQuestions == 0 ? 0 : (int)Math.Round((double)s.Score / s.TotalQuestions * 100))))
            .ForMember(d => d.Passed, o => o.MapFrom(s =>
                s.TotalQuestions == 0 ? false : (double)s.Score / s.TotalQuestions * 100 >= 50));
    }

    private static string CalcGrade(int pct) => pct switch
    {
        >= 90 => "A+",
        >= 80 => "A",
        >= 70 => "B",
        >= 60 => "C",
        >= 50 => "D",
        _ => "F"
    };
}
