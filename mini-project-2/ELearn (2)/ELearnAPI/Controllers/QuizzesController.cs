using ELearnAPI.DTOs;
using ELearnAPI.Services;
using Microsoft.AspNetCore.Mvc;

namespace ELearnAPI.Controllers;

[ApiController]
[Route("api/quizzes")]
public class QuizzesController(IQuizService quizService) : ControllerBase
{
    // GET /api/quizzes/by-course/1
    [HttpGet("by-course/{courseId}")]
    public async Task<IActionResult> GetByCourse(int courseId) =>
        Ok(await quizService.GetByCourseAsync(courseId));

    // POST /api/quizzes
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateQuizDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var quiz = await quizService.CreateAsync(dto);
        return CreatedAtAction(nameof(GetByCourse), new { courseId = quiz.CourseId }, quiz);
    }

    // GET /api/quizzes/1/questions
    [HttpGet("{quizId}/questions")]
    public async Task<IActionResult> GetQuestions(int quizId) =>
        Ok(await quizService.GetQuestionsAsync(quizId));

    // POST /api/quizzes/1/submit
    [HttpPost("{quizId}/submit")]
    public async Task<IActionResult> Submit(int quizId, [FromBody] QuizSubmitDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var result = await quizService.SubmitAsync(quizId, dto);
        return result is null ? NotFound(new { message = "Quiz not found." }) : Ok(result);
    }
}

[ApiController]
[Route("api/questions")]
public class QuestionsController(IQuizService quizService) : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateQuestionDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var question = await quizService.AddQuestionAsync(dto);
        return CreatedAtAction(nameof(Create), new { id = question.QuestionId }, question);
    }
}

[ApiController]
[Route("api/results")]
public class ResultsController(IResultService resultService) : ControllerBase
{
    [HttpGet("{userId}")]
    public async Task<IActionResult> GetByUser(int userId) =>
        Ok(await resultService.GetByUserAsync(userId));

    [HttpGet("above-average")]
    public async Task<IActionResult> GetAboveAverage() =>
        Ok(await resultService.GetAboveAverageAsync());
}
