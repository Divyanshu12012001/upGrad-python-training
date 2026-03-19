// dashboard.js — Dashboard page logic

document.addEventListener("DOMContentLoaded", () => {
  const profile = Storage.getProfile();
  const completed = Storage.getCompletedCourses();
  const quizHistory = Storage.getQuizHistory();

  // Welcome heading
  document.getElementById("welcomeHeading").textContent =
    `Welcome back, ${profile.name}! 👋`;

  // Stats
  document.getElementById("totalCourses").textContent = courses.length;
  document.getElementById("completedCount").textContent = completed.length;
  document.getElementById("quizzesTaken").textContent = quizHistory.length;

  if (quizHistory.length > 0) {
    const best = Math.max(...quizHistory.map((r) => r.percentage));
    document.getElementById("bestScore").textContent = best + "%";
  }

  // Course cards
  const container = document.getElementById("courseCardsContainer");
  container.innerHTML = courses
    .map((course) => {
      const done = Storage.isCourseCompleted(course.id);
      return `
        <article class="course-card" aria-label="${course.title}">
          <div class="course-card-icon">${course.icon}</div>
          <div class="course-card-title">${course.title}</div>
          <p class="course-card-desc">${course.description}</p>
          <div class="course-card-meta">
            <span class="badge-category">${course.category}</span>
            <span>⏱ ${course.duration}</span>
            <span>📖 ${course.lessons.length} lessons</span>
          </div>
          <div class="mb-2">
            <div class="progress-label">
              <span>Progress</span>
              <span>${done ? "100" : "0"}%</span>
            </div>
            <progress value="${done ? 100 : 0}" max="100"
              aria-label="${course.title} completion progress"></progress>
          </div>
          ${done ? '<span class="completed-badge">✅ Completed</span>' : ""}
          <a href="courses.html" class="btn-primary-custom mt-2 d-inline-block text-center"
            style="width:100%;text-decoration:none;">
            ${done ? "Review Course" : "Start Learning"}
          </a>
        </article>`;
    })
    .join("");

  // Overall progress
  const pct = Math.round((completed.length / courses.length) * 100);
  document.getElementById("overallProgressSection").innerHTML = `
    <div class="progress-label">
      <span>Courses Completed</span>
      <span>${completed.length} / ${courses.length}</span>
    </div>
    <progress value="${pct}" max="100" aria-label="Overall course completion"></progress>
    <div class="progress-label mt-1">
      <span class="fw-semibold" style="color:var(--primary)">${pct}% Complete</span>
    </div>
    ${courses
      .map(
        (c) => `
      <div class="mt-3">
        <div class="progress-label">
          <span>${c.icon} ${c.title}</span>
          <span>${Storage.isCourseCompleted(c.id) ? "100" : "0"}%</span>
        </div>
        <progress value="${Storage.isCourseCompleted(c.id) ? 100 : 0}"
          max="100" aria-label="${c.title} progress"></progress>
      </div>`
      )
      .join("")}`;

  // Recent activity
  const activityEl = document.getElementById("recentActivity");
  const activities = [];

  quizHistory.slice(0, 3).forEach((r) => {
    activities.push({
      icon: "📝",
      text: `Quiz completed — ${r.score}/${r.total} (${r.percentage}%)`,
      time: new Date(r.date).toLocaleDateString(),
    });
  });

  completed.slice(0, 3).forEach((id) => {
    const c = courses.find((x) => x.id === id);
    if (c)
      activities.push({ icon: "✅", text: `Completed: ${c.title}`, time: "Recently" });
  });

  if (activities.length === 0) {
    activityEl.innerHTML = `<p class="text-muted small">No recent activity yet.</p>`;
  } else {
    activityEl.innerHTML = activities
      .map(
        (a) => `
      <div class="activity-item">
        <span class="activity-dot"></span>
        <div>
          <div>${a.icon} ${a.text}</div>
          <div class="text-muted" style="font-size:0.75rem">${a.time}</div>
        </div>
      </div>`
      )
      .join("");
  }
});
