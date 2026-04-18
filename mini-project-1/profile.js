// profile.js — Profile page logic

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  renderProgress();
  renderCompletedCourses();
  renderQuizHistory();
  setupForm();
});

function loadProfile() {
  const p = Storage.getProfile();
  const initials = p.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  document.getElementById("avatarDisplay").textContent = initials;
  document.getElementById("profileName").textContent = p.name;
  document.getElementById("profileEmail").textContent = p.email;
  document.getElementById("infoName").textContent = p.name;
  document.getElementById("infoEmail").textContent = p.email;
  document.getElementById("infoBio").textContent = p.bio;
  document.getElementById("infoCompleted").textContent =
    `${Storage.getCompletedCourses().length} completed`;
  document.getElementById("infoQuizzes").textContent =
    `${Storage.getQuizHistory().length} taken`;

  // Pre-fill form
  document.getElementById("editName").value = p.name;
  document.getElementById("editEmail").value = p.email;
  document.getElementById("editBio").value = p.bio;
}

function renderProgress() {
  const completed = Storage.getCompletedCourses();
  const pct = Math.round((completed.length / courses.length) * 100);

  document.getElementById("progressOverview").innerHTML = `
    <div class="progress-label mb-1">
      <span class="fw-semibold">Overall Completion</span>
      <span class="fw-bold" style="color:var(--primary)">${pct}%</span>
    </div>
    <progress value="${pct}" max="100" aria-label="Overall learning progress"
      style="height:12px;"></progress>
    <div class="row g-3 mt-2">
      ${courses
        .map((c) => {
          const done = Storage.isCourseCompleted(c.id);
          return `
            <div class="col-sm-6">
              <div class="d-flex justify-content-between mb-1" style="font-size:0.85rem;">
                <span>${c.icon} ${c.title}</span>
                <span>${done ? "100" : "0"}%</span>
              </div>
              <progress value="${done ? 100 : 0}" max="100"
                aria-label="${c.title} progress"></progress>
            </div>`;
        })
        .join("")}
    </div>`;
}

function renderCompletedCourses() {
  const completedIds = Storage.getCompletedCourses();
  const el = document.getElementById("completedCoursesList");

  if (completedIds.length === 0) {
    el.innerHTML = `<p class="text-muted small">No courses completed yet. <a href="courses.html">Browse courses →</a></p>`;
    return;
  }

  const completedCourses = courses.filter((c) => completedIds.includes(c.id));
  el.innerHTML = `
    <div class="course-cards-container">
      ${completedCourses
        .map(
          (c) => `
        <div class="course-card" style="flex:1 1 220px;" aria-label="${c.title}">
          <div class="course-card-icon">${c.icon}</div>
          <div class="course-card-title">${c.title}</div>
          <div class="course-card-meta">
            <span class="badge-category">${c.category}</span>
            <span>⏱ ${c.duration}</span>
          </div>
          <span class="completed-badge">✅ Completed</span>
          <div class="mt-2">
            <progress value="100" max="100" aria-label="${c.title} complete"></progress>
          </div>
        </div>`
        )
        .join("")}
    </div>`;
}

function renderQuizHistory() {
  const history = Storage.getQuizHistory();
  const el = document.getElementById("quizHistoryList");

  if (history.length === 0) {
    el.innerHTML = `<p class="text-muted small">No quizzes taken yet. <a href="quiz.html">Take a quiz →</a></p>`;
    return;
  }

  el.innerHTML = `
    <div class="table-wrapper">
      <table class="table table-hover mb-0" data-type="courses" aria-label="Quiz history">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Date</th>
            <th scope="col">Score</th>
            <th scope="col">Percentage</th>
            <th scope="col">Grade</th>
            <th scope="col">Result</th>
          </tr>
        </thead>
        <tbody>
          ${history
            .map(
              (r, i) => `
            <tr>
              <td>${i + 1}</td>
              <td>${new Date(r.date).toLocaleDateString()}</td>
              <td>${r.score} / ${r.total}</td>
              <td>
                <progress value="${r.percentage}" max="100"
                  aria-label="${r.percentage}% score" style="width:80px;"></progress>
                <span class="ms-1">${r.percentage}%</span>
              </td>
              <td><strong>${r.grade}</strong></td>
              <td>
                ${r.passed
                  ? `<span class="completed-badge">✅ Passed</span>`
                  : `<span class="badge bg-danger">❌ Failed</span>`}
              </td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function setupForm() {
  document.getElementById("profileForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("editName").value.trim();
    const email = document.getElementById("editEmail").value.trim();
    const bio = document.getElementById("editBio").value.trim();

    // Basic validation
    if (!name || !email) {
      alert("Name and email are required.");
      return;
    }

    const initials = name
      .split(" ")
      .map((w) => w[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

    Storage.saveProfile({ name, email, bio, avatar: initials });
    loadProfile();

    const msg = document.getElementById("saveMsg");
    msg.style.display = "block";
    setTimeout(() => (msg.style.display = "none"), 3000);
  });
}
