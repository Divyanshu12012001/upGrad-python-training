// dashboard.js — API-connected dashboard

document.addEventListener('DOMContentLoaded', async () => {
  if (Auth.redirectIfNotLoggedIn()) return;
  const userId = Auth.getUserId();
  document.getElementById('welcomeHeading').textContent = `Welcome back, ${Auth.getUserName()}! 👋`;

  try {
    const [courses, results] = await Promise.all([
      Api.get('/courses'),
      Api.get(`/results/${userId}`)
    ]);

    document.getElementById('totalCourses').textContent = courses.length;
    document.getElementById('quizzesTaken').textContent = results.length;

    const best = results.length
      ? Math.max(...results.map(r => r.percentage)) + '%'
      : '—';
    document.getElementById('bestScore').textContent = best;

    const passed = results.filter(r => r.passed).length;
    document.getElementById('completedCount').textContent = passed;

    // Course cards
    document.getElementById('courseCardsContainer').innerHTML = courses.map(course => `
      <article class="course-card" aria-label="${course.title}">
        <div class="course-card-icon">${course.icon || '📚'}</div>
        <div class="course-card-title">${course.title}</div>
        <p class="course-card-desc">${course.description}</p>
        <div class="course-card-meta">
          <span class="badge-category">${course.category}</span>
          <span>⏱ ${course.duration}</span>
          <span>📖 ${course.lessonCount} lessons</span>
        </div>
        <a href="courses.html" class="btn-primary-custom mt-2 d-inline-block text-center" style="width:100%;text-decoration:none;">
          Start Learning
        </a>
      </article>`).join('');

    // Overall progress
    const pct = courses.length ? Math.round(passed / courses.length * 100) : 0;
    document.getElementById('overallProgressSection').innerHTML = `
      <div class="progress-label"><span>Quizzes Passed</span><span>${passed} / ${courses.length}</span></div>
      <progress value="${pct}" max="100" aria-label="Overall progress"></progress>
      <div class="progress-label mt-1"><span class="fw-semibold" style="color:var(--primary)">${pct}% Complete</span></div>`;

    // Recent activity
    const activities = results.slice(0, 5).map(r => ({
      icon: '📝',
      text: `${r.quizTitle} — ${r.score}/${r.totalQuestions} (${r.percentage}%)`,
      time: new Date(r.attemptDate).toLocaleDateString()
    }));

    document.getElementById('recentActivity').innerHTML = activities.length === 0
      ? `<p class="text-muted small">No recent activity yet.</p>`
      : activities.map(a => `
          <div class="activity-item">
            <span class="activity-dot"></span>
            <div><div>${a.icon} ${a.text}</div><div class="text-muted" style="font-size:0.75rem">${a.time}</div></div>
          </div>`).join('');

  } catch (err) {
    console.error('Dashboard load error:', err);
    document.getElementById('courseCardsContainer').innerHTML =
      `<p class="text-danger">⚠️ Failed to load data. Ensure the API is running.</p>`;
  }
});
