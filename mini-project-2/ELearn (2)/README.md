# ELearn — Full-Stack E-Learning Platform

ASP.NET Core 8 Web API + HTML/CSS/Bootstrap frontend.

---

## Project Structure

```
ELearn (2)/
├── ELearn/                  # Frontend (HTML, CSS, JS)
│   ├── login.html           # Login & Register page
│   ├── dashboard.html
│   ├── courses.html
│   ├── quiz.html
│   ├── profile.html
│   ├── api.js               # Shared fetch client + Auth helpers
│   └── styles.css
└── ELearnAPI/               # Backend (.NET 8)
    ├── Controllers/
    ├── Services/
    ├── Repositories/
    ├── DTOs/
    ├── Models/
    ├── Data/                # DbContext + AutoMapper profile
    ├── Migrations/
    ├── Tests/               # xUnit unit tests
    ├── database.sql         # SQL Server scripts
    ├── ELearn.postman_collection.json
    ├── DataSeeder.cs
    └── Program.cs
```

---

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- [Node.js](https://nodejs.org) (for Jest frontend tests only)
- A browser (no web server needed for frontend)

---

## Setup & Run

### 1. Restore & build the API

```bash
cd "ELearn (2)/ELearnAPI"
dotnet restore
dotnet build
```

### 2. Apply database migrations

The project uses **SQLite** (file-based, no install needed).

```bash
dotnet ef database update
```

> The database file `ELearnDB.sqlite` is created automatically.  
> Seed data (4 courses, quizzes, questions, admin user) is inserted on first run.

### 3. Run the API

```bash
dotnet run
```

API runs at: `http://localhost:5000`  
Swagger UI: `http://localhost:5000/swagger`

### 4. Open the frontend

Open `ELearn/login.html` directly in your browser (no server needed).

**Demo credentials:**
- Email: `admin@elearn.com`
- Password: `Admin123!`

---

## Authentication Flow

1. Open `login.html` → enter credentials → click Login
2. On success the API returns a JWT token stored in `sessionStorage`
3. All subsequent API calls send `Authorization: Bearer <token>`
4. All pages redirect to `login.html` if no token is present

---

## Running Tests

### C# unit tests (xUnit)

```bash
cd "ELearn (2)/ELearnAPI/Tests"
dotnet test
```

Tests cover:
- Quiz scoring & grade calculation
- Pass/fail logic
- CourseService CRUD (mocked repository)
- UserService register & login (mocked repository)
- LINQ filtering, ordering, grouping
- Exception propagation

### JavaScript unit tests (Jest)

```bash
cd "ELearn (2)/ELearn"
npm install
npm test
```

Tests cover: `calculateGrade`, `calculatePercentage`, `isPassed`, `getPerformanceFeedback`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/users/register | Register new user |
| POST | /api/users/login | Login, returns JWT |
| GET | /api/users/{id} | Get user profile |
| PUT | /api/users/{id} | Update profile |
| GET | /api/courses | List all courses |
| GET | /api/courses/{id} | Get course by id |
| POST | /api/courses | Create course |
| PUT | /api/courses/{id} | Update course |
| DELETE | /api/courses/{id} | Delete course |
| GET | /api/courses/{id}/lessons | Get lessons for course |
| POST | /api/lessons | Create lesson |
| PUT | /api/lessons/{id} | Update lesson |
| DELETE | /api/lessons/{id} | Delete lesson |
| GET | /api/quizzes/by-course/{courseId} | Get quizzes for course |
| POST | /api/quizzes | Create quiz |
| GET | /api/quizzes/{quizId}/questions | Get questions |
| POST | /api/questions | Add question |
| POST | /api/quizzes/{quizId}/submit | Submit quiz attempt |
| GET | /api/results/{userId} | Get user results |
| GET | /api/results/above-average | Users above average score |

---

## Postman

Import `ELearnAPI/ELearn.postman_collection.json` into Postman.

Run **Login** first — the test script automatically saves the JWT token and userId as collection variables used by all other requests.

---

## Switch to SQL Server (optional)

1. Replace the SQLite package in `ELearnAPI.csproj`:
   ```xml
   <!-- Remove -->
   <PackageReference Include="Microsoft.EntityFrameworkCore.Sqlite" Version="8.0.0" />
   <!-- Add -->
   <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="8.0.0" />
   ```

2. Update `Program.cs`:
   ```csharp
   // Replace UseSqlite with:
   opt.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"))
   ```

3. Update `appsettings.json`:
   ```json
   "DefaultConnection": "Server=localhost;Database=ELearnDB;Trusted_Connection=True;TrustServerCertificate=True;"
   ```

4. Re-run migrations:
   ```bash
   dotnet ef migrations add InitialCreate
   dotnet ef database update
   ```

The `database.sql` file contains equivalent SQL Server scripts for manual execution.

---

## JWT Configuration

Configured in `appsettings.json`:

```json
"Jwt": {
  "Key": "ELearnDefaultSecretKey_ChangeInProduction_32chars!",
  "Issuer": "ELearnAPI",
  "Audience": "ELearnFrontend"
}
```

Change the `Key` value before deploying to production.
