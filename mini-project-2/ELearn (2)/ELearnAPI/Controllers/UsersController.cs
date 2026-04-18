using ELearnAPI.DTOs;
using ELearnAPI.Services;
using Microsoft.AspNetCore.Mvc;

namespace ELearnAPI.Controllers;

[ApiController]
[Route("api/users")]
public class UsersController(IUserService service) : ControllerBase
{
    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] RegisterDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var user = await service.RegisterAsync(dto);
        return user is null
            ? Conflict(new { message = "Email already registered." })
            : CreatedAtAction(nameof(GetById), new { id = user.UserId }, user);
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var response = await service.LoginAsync(dto);
        return response is null
            ? Unauthorized(new { message = "Invalid email or password." })
            : Ok(response);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var user = await service.GetByIdAsync(id);
        return user is null ? NotFound() : Ok(user);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateUserDto dto)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);
        var user = await service.UpdateAsync(id, dto);
        return user is null ? NotFound() : Ok(user);
    }
}
