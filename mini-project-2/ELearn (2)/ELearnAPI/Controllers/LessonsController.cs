using ELearnAPI.DTOs;
using ELearnAPI.Services;
using Microsoft.AspNetCore.Mvc;

namespace ELearnAPI.Controllers;

[ApiController]
[Route("api/lessons")]
public class LessonsController(ILessonService service) : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateLessonDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var lesson = await service.CreateAsync(dto);
        return CreatedAtAction(nameof(Update), new { id = lesson.LessonId }, lesson);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateLessonDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var lesson = await service.UpdateAsync(id, dto);
        return lesson is null ? NotFound() : Ok(lesson);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var deleted = await service.DeleteAsync(id);
        return deleted ? NoContent() : NotFound();
    }
}
