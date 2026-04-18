-- ============================================================
-- ELearnDB SQL Scripts
-- ============================================================

-- ── CREATE DATABASE ──
CREATE DATABASE ELearnDB;
GO
USE ELearnDB;
GO

-- ── TABLES ──
CREATE TABLE Users (
    UserId      INT IDENTITY(1,1) PRIMARY KEY,
    FullName    NVARCHAR(200) NOT NULL,
    Email       NVARCHAR(200) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(MAX) NOT NULL,
    Bio         NVARCHAR(500) NULL,
    CreatedAt   DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE Courses (
    CourseId    INT IDENTITY(1,1) PRIMARY KEY,
    Title       NVARCHAR(300) NOT NULL,
    Description NVARCHAR(MAX),
    Category    NVARCHAR(100),
    Duration    NVARCHAR(50),
    Icon        NVARCHAR(20),
    CreatedBy   INT NOT NULL REFERENCES Users(UserId),
    CreatedAt   DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE Lessons (
    LessonId    INT IDENTITY(1,1) PRIMARY KEY,
    CourseId    INT NOT NULL REFERENCES Courses(CourseId) ON DELETE CASCADE,
    Title       NVARCHAR(300) NOT NULL,
    Content     NVARCHAR(MAX),
    OrderIndex  INT NOT NULL DEFAULT 0
);

CREATE TABLE Quizzes (
    QuizId      INT IDENTITY(1,1) PRIMARY KEY,
    CourseId    INT NOT NULL REFERENCES Courses(CourseId) ON DELETE CASCADE,
    Title       NVARCHAR(300) NOT NULL
);

CREATE TABLE Questions (
    QuestionId  INT IDENTITY(1,1) PRIMARY KEY,
    QuizId      INT NOT NULL REFERENCES Quizzes(QuizId) ON DELETE CASCADE,
    QuestionText NVARCHAR(MAX) NOT NULL,
    OptionA     NVARCHAR(500) NOT NULL,
    OptionB     NVARCHAR(500) NOT NULL,
    OptionC     NVARCHAR(500) NOT NULL,
    OptionD     NVARCHAR(500) NOT NULL,
    CorrectAnswer CHAR(1) NOT NULL CHECK (CorrectAnswer IN ('A','B','C','D'))
);

CREATE TABLE Results (
    ResultId        INT IDENTITY(1,1) PRIMARY KEY,
    UserId          INT NOT NULL REFERENCES Users(UserId) ON DELETE CASCADE,
    QuizId          INT NOT NULL REFERENCES Quizzes(QuizId),
    Score           INT NOT NULL,
    TotalQuestions  INT NOT NULL,
    AttemptDate     DATETIME2 DEFAULT GETUTCDATE()
);
GO

-- ── SEED DATA ──
INSERT INTO Users (FullName, Email, PasswordHash) VALUES
('Admin User', 'admin@elearn.com', 'hashed_password_here');

INSERT INTO Courses (Title, Description, Category, Duration, Icon, CreatedBy) VALUES
('HTML & CSS Fundamentals', 'Learn the building blocks of the web.', 'Web Development', '4 hours', N'🌐', 1),
('JavaScript Essentials',   'Master core JavaScript concepts.',       'Programming',     '6 hours', N'⚡', 1),
('Bootstrap Framework',     'Build responsive UIs quickly.',          'Web Development', '3 hours', N'🎨', 1),
('Python for Beginners',    'Start your programming journey.',        'Programming',     '8 hours', N'🐍', 1);

INSERT INTO Lessons (CourseId, Title, Content, OrderIndex) VALUES
(1, 'Introduction to HTML',       'HTML basics and structure.',    1),
(1, 'HTML Elements & Attributes', 'Tags, attributes, and values.', 2),
(1, 'CSS Selectors & Properties', 'Styling with CSS.',             3),
(1, 'Box Model & Layout',         'Understanding the box model.',  4),
(1, 'Responsive Design Basics',   'Media queries and flexbox.',    5),
(2, 'Variables & Data Types',     'JS variables and types.',       1),
(2, 'Functions & Scope',          'Function declarations.',        2),
(2, 'DOM Manipulation',           'Selecting and modifying DOM.',  3),
(2, 'Events & Listeners',         'Handling user events.',         4),
(2, 'Async JavaScript',           'Promises and async/await.',     5);

INSERT INTO Quizzes (CourseId, Title) VALUES
(1, 'HTML & CSS Quiz'),
(2, 'JavaScript Quiz'),
(3, 'Bootstrap Quiz'),
(4, 'Python Quiz');

INSERT INTO Questions (QuizId, QuestionText, OptionA, OptionB, OptionC, OptionD, CorrectAnswer) VALUES
(1, 'Which HTML tag defines an unordered list?', '<ol>', '<ul>', '<li>', '<list>', 'B'),
(1, 'Which CSS property controls text size?', 'font-weight', 'text-size', 'font-size', 'text-style', 'C'),
(2, 'What does DOM stand for?', 'Document Object Model', 'Data Object Management', 'Document Oriented Model', 'Dynamic Object Module', 'A'),
(2, 'Which keyword declares a block-scoped variable?', 'var', 'let', 'define', 'set', 'B'),
(2, 'What is typeof null in JavaScript?', 'null', 'undefined', 'object', 'string', 'C'),
(3, 'Which Bootstrap class creates a responsive container?', '.wrapper', '.container', '.box', '.grid', 'B'),
(4, 'Which Python function prints to console?', 'echo()', 'console.log()', 'print()', 'write()', 'C');
GO

-- ============================================================
-- QUERY EXAMPLES
-- ============================================================

-- SELECT with WHERE and ORDER BY
SELECT CourseId, Title, Category, Duration
FROM Courses
WHERE Category = 'Programming'
ORDER BY CreatedAt DESC;

-- INNER JOIN: Courses with creator name
SELECT c.CourseId, c.Title, u.FullName AS CreatedBy
FROM Courses c
INNER JOIN Users u ON c.CreatedBy = u.UserId;

-- LEFT JOIN: All courses with lesson count (including courses with 0 lessons)
SELECT c.Title, COUNT(l.LessonId) AS LessonCount
FROM Courses c
LEFT JOIN Lessons l ON c.CourseId = l.CourseId
GROUP BY c.CourseId, c.Title
ORDER BY LessonCount DESC;

-- GROUP BY + COUNT + AVG: Quiz stats per user
SELECT u.FullName, COUNT(r.ResultId) AS QuizzesTaken,
       AVG(CAST(r.Score AS FLOAT) / r.TotalQuestions * 100) AS AvgScore
FROM Results r
INNER JOIN Users u ON r.UserId = u.UserId
GROUP BY u.UserId, u.FullName
ORDER BY AvgScore DESC;

-- SUBQUERY: Users scoring above average
SELECT u.FullName, r.Score, r.TotalQuestions
FROM Results r
INNER JOIN Users u ON r.UserId = u.UserId
WHERE (CAST(r.Score AS FLOAT) / r.TotalQuestions * 100) >
    (SELECT AVG(CAST(Score AS FLOAT) / TotalQuestions * 100) FROM Results);

-- UNION: Combined activity feed (quiz attempts + course completions placeholder)
SELECT UserId, 'Quiz Attempt' AS ActivityType, CAST(AttemptDate AS NVARCHAR) AS ActivityDate
FROM Results
UNION
SELECT CreatedBy, 'Course Created' AS ActivityType, CAST(CreatedAt AS NVARCHAR) AS ActivityDate
FROM Courses
ORDER BY ActivityDate DESC;

-- INSERT
INSERT INTO Results (UserId, QuizId, Score, TotalQuestions) VALUES (1, 1, 8, 10);

-- UPDATE
UPDATE Users SET FullName = 'Updated Name' WHERE UserId = 1;

-- DELETE
DELETE FROM Results WHERE ResultId = 1;
GO
