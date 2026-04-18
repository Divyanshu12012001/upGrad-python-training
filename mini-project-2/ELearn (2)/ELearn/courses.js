// courses.js — API-connected courses page

let allCourses = [];

async function loadCourses() {
  try {
    allCourses = await Api.get('/courses');
    renderCards(allCourses);
    renderTable(allCourses);
    await renderLessonCards(allCourses);
  } catch (err) {
    console.error('Courses load error:', err);
    document.getElementById('courseCardsContainer').innerHTML =
      `<p class="text-danger">⚠️ Failed to load courses. Ensure the API is running.</p>`;
  }
}

function renderCards(list) {
  document.getElementById('courseCardsContainer').innerHTML = list.map(course => `
    <article class="course-card" aria-label="${course.title}">
      <div class="course-card-icon">${course.icon || '📚'}</div>
      <div class="course-card-title">${course.title}</div>
      <p class="course-card-desc">${course.description}</p>
      <div class="course-card-meta">
        <span class="badge-category">${course.category}</span>
        <span>⏱ ${course.duration}</span>
        <span>📖 ${course.lessonCount} lessons</span>
      </div>
      <a href="quiz.html?courseId=${course.courseId}" class="btn-primary-custom w-100 mt-2 d-inline-block text-center" style="text-decoration:none;">
        Start Learning
      </a>
    </article>`).join('');
}

function renderTable(list) {
  document.getElementById('courseTableBody').innerHTML = list.map((course, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${course.icon || '📚'} ${course.title}</strong></td>
      <td><span class="badge-category">${course.category}</span></td>
      <td>${course.duration}</td>
      <td>${course.lessonCount}</td>
      <td><span class="badge bg-warning text-dark">In Progress</span></td>
      <td><a href="quiz.html?courseId=${course.courseId}" class="btn btn-sm btn-outline-primary">Take Quiz</a></td>
    </tr>`).join('');
}

async function renderLessonCards(list) {
  const lessonData = await Promise.all(
    list.map(c => Api.get(`/courses/${c.courseId}/lessons`).catch(() => []))
  );
  document.getElementById('lessonCards').innerHTML = list.map((course, i) => `
    <div class="col-md-6">
      <div class="sidebar-card h-100">
        <h5>${course.icon || '📚'} ${course.title}</h5>
        <ol class="lesson-list" aria-label="Lessons for ${course.title}">
          ${lessonData[i].length
            ? lessonData[i].map(l => `<li>${l.title}</li>`).join('')
            : '<li class="text-muted">No lessons yet.</li>'}
        </ol>
      </div>
    </div>`).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  if (Auth.redirectIfNotLoggedIn()) return;
  loadCourses();

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.remove('active', 'btn-primary');
        b.classList.add('btn-outline-primary');
      });
      btn.classList.add('active', 'btn-primary');
      btn.classList.remove('btn-outline-primary');
      const filtered = btn.dataset.filter === 'all'
        ? allCourses
        : allCourses.filter(c => c.category === btn.dataset.filter);
      renderCards(filtered);
      renderTable(filtered);
    });
  });
});
