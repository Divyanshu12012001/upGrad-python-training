using ELearnAPI.Data;
using ELearnAPI.Models;
using Microsoft.EntityFrameworkCore;

namespace ELearnAPI;

public static class DataSeeder
{
    public static async Task SeedAsync(AppDbContext db)
    {
        if (await db.Users.AnyAsync()) return; // already seeded

        var admin = new User
        {
            FullName = "Admin User",
            Email = "admin@elearn.com",
            PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!"),
            Bio = "Platform administrator"
        };
        db.Users.Add(admin);
        await db.SaveChangesAsync();

        var courses = new List<Course>
        {
            new() { Title = "HTML & CSS Fundamentals", Description = "Learn the building blocks of the web with HTML and CSS.", Category = "Web Development", Duration = "4 hours", Icon = "🌐", CreatedBy = admin.UserId },
            new() { Title = "JavaScript Essentials",   Description = "Master core JavaScript concepts for modern web development.", Category = "Programming",     Duration = "6 hours", Icon = "⚡", CreatedBy = admin.UserId },
            new() { Title = "Bootstrap Framework",     Description = "Build responsive UIs quickly using Bootstrap 5.", Category = "Web Development", Duration = "3 hours", Icon = "🎨", CreatedBy = admin.UserId },
            new() { Title = "Python for Beginners",    Description = "Start your programming journey with Python.", Category = "Programming",     Duration = "8 hours", Icon = "🐍", CreatedBy = admin.UserId },
        };
        db.Courses.AddRange(courses);
        await db.SaveChangesAsync();

        var lessons = new List<Lesson>
        {
            new() { CourseId = courses[0].CourseId, Title = "Introduction to HTML",       Content = "HTML basics and structure.",    OrderIndex = 1 },
            new() { CourseId = courses[0].CourseId, Title = "HTML Elements & Attributes", Content = "Tags, attributes, and values.", OrderIndex = 2 },
            new() { CourseId = courses[0].CourseId, Title = "CSS Selectors & Properties", Content = "Styling with CSS.",             OrderIndex = 3 },
            new() { CourseId = courses[0].CourseId, Title = "Box Model & Layout",         Content = "Understanding the box model.",  OrderIndex = 4 },
            new() { CourseId = courses[0].CourseId, Title = "Responsive Design Basics",   Content = "Media queries and flexbox.",    OrderIndex = 5 },
            new() { CourseId = courses[1].CourseId, Title = "Variables & Data Types",     Content = "JS variables and types.",       OrderIndex = 1 },
            new() { CourseId = courses[1].CourseId, Title = "Functions & Scope",          Content = "Function declarations.",        OrderIndex = 2 },
            new() { CourseId = courses[1].CourseId, Title = "DOM Manipulation",           Content = "Selecting and modifying DOM.",  OrderIndex = 3 },
            new() { CourseId = courses[1].CourseId, Title = "Events & Listeners",         Content = "Handling user events.",         OrderIndex = 4 },
            new() { CourseId = courses[1].CourseId, Title = "Async JavaScript",           Content = "Promises and async/await.",     OrderIndex = 5 },
            new() { CourseId = courses[2].CourseId, Title = "Grid System",                Content = "Bootstrap grid layout.",        OrderIndex = 1 },
            new() { CourseId = courses[2].CourseId, Title = "Components Overview",        Content = "Bootstrap components.",         OrderIndex = 2 },
            new() { CourseId = courses[2].CourseId, Title = "Utility Classes",            Content = "Bootstrap utilities.",          OrderIndex = 3 },
            new() { CourseId = courses[3].CourseId, Title = "Python Syntax & Variables",  Content = "Python basics.",                OrderIndex = 1 },
            new() { CourseId = courses[3].CourseId, Title = "Control Flow",               Content = "If, loops in Python.",          OrderIndex = 2 },
        };
        db.Lessons.AddRange(lessons);

        var quizzes = new List<Quiz>
        {
            new() { CourseId = courses[0].CourseId, Title = "HTML & CSS Quiz" },
            new() { CourseId = courses[1].CourseId, Title = "JavaScript Quiz" },
            new() { CourseId = courses[2].CourseId, Title = "Bootstrap Quiz" },
            new() { CourseId = courses[3].CourseId, Title = "Python Quiz" },
        };
        db.Quizzes.AddRange(quizzes);
        await db.SaveChangesAsync();

        var questions = new List<Question>
        {
            new() { QuizId = quizzes[0].QuizId, QuestionText = "Which HTML tag defines an unordered list?", OptionA = "<ol>", OptionB = "<ul>", OptionC = "<li>", OptionD = "<list>", CorrectAnswer = "B" },
            new() { QuizId = quizzes[0].QuizId, QuestionText = "Which CSS property controls text size?",    OptionA = "font-weight", OptionB = "text-size", OptionC = "font-size", OptionD = "text-style", CorrectAnswer = "C" },
            new() { QuizId = quizzes[0].QuizId, QuestionText = "What does CSS stand for?",                  OptionA = "Computer Style Sheets", OptionB = "Creative Style Syntax", OptionC = "Cascading Style Sheets", OptionD = "Colorful Style Sheets", CorrectAnswer = "C" },
            new() { QuizId = quizzes[1].QuizId, QuestionText = "What does DOM stand for?",                  OptionA = "Document Object Model", OptionB = "Data Object Management", OptionC = "Document Oriented Model", OptionD = "Dynamic Object Module", CorrectAnswer = "A" },
            new() { QuizId = quizzes[1].QuizId, QuestionText = "Which keyword declares a block-scoped variable?", OptionA = "var", OptionB = "let", OptionC = "define", OptionD = "set", CorrectAnswer = "B" },
            new() { QuizId = quizzes[1].QuizId, QuestionText = "What is typeof null in JavaScript?",        OptionA = "null", OptionB = "undefined", OptionC = "object", OptionD = "string", CorrectAnswer = "C" },
            new() { QuizId = quizzes[1].QuizId, QuestionText = "Which method adds an element at the end of an array?", OptionA = "push()", OptionB = "pop()", OptionC = "shift()", OptionD = "append()", CorrectAnswer = "A" },
            new() { QuizId = quizzes[2].QuizId, QuestionText = "Which Bootstrap class creates a responsive container?", OptionA = ".wrapper", OptionB = ".container", OptionC = ".box", OptionD = ".grid", CorrectAnswer = "B" },
            new() { QuizId = quizzes[3].QuizId, QuestionText = "Which Python function prints to console?",  OptionA = "echo()", OptionB = "console.log()", OptionC = "print()", OptionD = "write()", CorrectAnswer = "C" },
            new() { QuizId = quizzes[3].QuizId, QuestionText = "What is the correct arrow function syntax in JavaScript?", OptionA = "function => () {}", OptionB = "const fn = () => {}", OptionC = "fn() -> {}", OptionD = "arrow fn() {}", CorrectAnswer = "B" },
        };
        db.Questions.AddRange(questions);
        await db.SaveChangesAsync();
    }
}
