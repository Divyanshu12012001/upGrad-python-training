// courses.js — Courses page logic

document.addEventListener("DOMContentLoaded", () => {
  renderCards(courses);
  renderTable(courses);
  renderLessonCards(courses);
  setupFilters();
});

function renderCards(list) {
  const container = document.getElementById("courseCardsContainer");
  container.innerHTML = list
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
          <div class="mb-3">
            <div class="progress-label">
              <span>Progress</span><span>${done ? "100" : "0"}%</span>
            </div>
            <progress value="${done ? 100 : 0}" max="100"
              aria-label="${course.title} completion"></progress>
          </div>
          ${done
            ? `<span class="completed-badge">✅ Completed</span>`
            : `<button class="btn-primary-custom w-100 mt-2"
                onclick="completeCourse(${course.id}, this)">
                Mark as Complete
               </button>`
          }
        </article>`;
    })
    .join("");
}

function renderTable(list) {
  const tbody = document.getElementById("courseTableBody");
  tbody.innerHTML = list
    .map(
      (course, i) => {
        const done = Storage.isCourseCompleted(course.id);
        return `
          <tr>
            <td>${i + 1}</td>
            <td><strong>${course.icon} ${course.title}</strong></td>
            <td><span class="badge-category">${course.category}</span></td>
            <td>${course.duration}</td>
            <td>${course.lessons.length}</td>
            <td>
              ${done
                ? `<span class="completed-badge">✅ Done</span>`
                : `<span class="badge bg-warning text-dark">In Progress</span>`}
            </td>
            <td>
              <a href="quiz.html" class="btn btn-sm btn-outline-primary">Take Quiz</a>
            </td>
          </tr>`;
      }
    )
    .join("");
}

function renderLessonCards(list) {
  const container = document.getElementById("lessonCards");
  container.innerHTML = list
    .map(
      (course) => `
        <div class="col-md-6">
          <div class="sidebar-card h-100">
            <h5>${course.icon} ${course.title}</h5>
            <ol class="lesson-list" aria-label="Lessons for ${course.title}">
              ${course.lessons.map((l) => `<li>${l}</li>`).join("")}
            </ol>
          </div>
        </div>`
    )
    .join("");
}

function setupFilters() {
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach((b) => {
        b.classList.remove("active", "btn-primary");
        b.classList.add("btn-outline-primary");
      });
      btn.classList.add("active", "btn-primary");
      btn.classList.remove("btn-outline-primary");

      const filter = btn.dataset.filter;
      const filtered =
        filter === "all" ? courses : courses.filter((c) => c.category === filter);
      renderCards(filtered);
      renderTable(filtered);
      renderLessonCards(filtered);
    });
  });
}

function completeCourse(courseId, btn) {
  Storage.completeCourse(courseId);
  btn.closest(".course-card").querySelector(".course-card-meta + div + button, .course-card-meta + div + *");

  // Refresh renders
  const activeFilter = document.querySelector(".filter-btn.active")?.dataset.filter || "all";
  const filtered =
    activeFilter === "all" ? courses : courses.filter((c) => c.category === activeFilter);
  renderCards(filtered);
  renderTable(filtered);

  // Show toast
  const toastEl = document.getElementById("completionToast");
  const course = courses.find((c) => c.id === courseId);
  document.getElementById("toastMsg").textContent = `✅ "${course.title}" marked as completed!`;
  new bootstrap.Toast(toastEl, { delay: 3000 }).show();
}
