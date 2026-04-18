// profile.js — API-connected profile page

document.addEventListener('DOMContentLoaded', async () => {
  if (Auth.redirectIfNotLoggedIn()) return;
  const userId = Auth.getUserId();

  try {
    const [user, results, courses] = await Promise.all([
      Api.get(`/users/${userId}`),
      Api.get(`/results/${userId}`),
      Api.get('/courses')
    ]);

    renderProfile(user, results);
    renderProgress(results, courses);
    renderQuizHistory(results);
  } catch (err) {
    console.error('Profile load error:', err);
  }

  document.getElementById('profileForm').addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('editName').value.trim();
    const email = document.getElementById('editEmail').value.trim();
    const bio = document.getElementById('editBio').value.trim();
    if (!name || !email) { alert('Name and email are required.'); return; }

    try {
      const updated = await Api.put(`/users/${userId}`, { fullName: name, email, bio });
      renderProfile(updated, null);
      Auth.setUser(updated.userId, updated.fullName);
      const msg = document.getElementById('saveMsg');
      msg.style.display = 'block';
      setTimeout(() => msg.style.display = 'none', 3000);
    } catch (err) {
      alert('Failed to update profile.');
    }
  });
});

function renderProfile(user, results) {
  if (!user) return;
  const initials = user.fullName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  document.getElementById('avatarDisplay').textContent = initials;
  document.getElementById('profileName').textContent = user.fullName;
  document.getElementById('profileEmail').textContent = user.email;
  document.getElementById('infoName').textContent = user.fullName;
  document.getElementById('infoEmail').textContent = user.email;
  document.getElementById('infoBio').textContent = user.bio || '—';
  if (results) {
    document.getElementById('infoQuizzes').textContent = `${results.length} taken`;
    document.getElementById('infoCompleted').textContent =
      `${results.filter(r => r.passed).length} passed`;
  }
  document.getElementById('editName').value = user.fullName;
  document.getElementById('editEmail').value = user.email;
  document.getElementById('editBio').value = user.bio || '';
}

function renderProgress(results, courses) {
  const passed = results.filter(r => r.passed).length;
  const pct = courses.length ? Math.round(passed / courses.length * 100) : 0;
  document.getElementById('progressOverview').innerHTML = `
    <div class="progress-label mb-1">
      <span class="fw-semibold">Overall Completion</span>
      <span class="fw-bold" style="color:var(--primary)">${pct}%</span>
    </div>
    <progress value="${pct}" max="100" aria-label="Overall learning progress" style="height:12px;"></progress>
    <p class="text-muted small mt-2">${passed} of ${courses.length} courses passed via quiz.</p>`;
}

function renderQuizHistory(results) {
  const el = document.getElementById('quizHistoryList');
  if (!results.length) {
    el.innerHTML = `<p class="text-muted small">No quizzes taken yet. <a href="quiz.html">Take a quiz →</a></p>`;
    return;
  }
  el.innerHTML = `
    <div class="table-wrapper">
      <table class="table table-hover mb-0" aria-label="Quiz history">
        <thead><tr><th>#</th><th>Quiz</th><th>Date</th><th>Score</th><th>%</th><th>Grade</th><th>Result</th></tr></thead>
        <tbody>
          ${results.map((r, i) => `
            <tr>
              <td>${i + 1}</td>
              <td>${r.quizTitle}</td>
              <td>${new Date(r.attemptDate).toLocaleDateString()}</td>
              <td>${r.score} / ${r.totalQuestions}</td>
              <td><progress value="${r.percentage}" max="100" style="width:60px;"></progress> ${r.percentage}%</td>
              <td><strong>${r.grade}</strong></td>
              <td>${r.passed
                ? `<span class="completed-badge">✅ Passed</span>`
                : `<span class="badge bg-danger">❌ Failed</span>`}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}
