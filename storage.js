// Web Storage helpers for cross-page state management

const Storage = {
  // Quiz results
  saveQuizResult(result) {
    const history = this.getQuizHistory();
    history.unshift(result);
    localStorage.setItem("quizHistory", JSON.stringify(history.slice(0, 10)));
  },
  getQuizHistory() {
    return JSON.parse(localStorage.getItem("quizHistory") || "[]");
  },
  getLatestResult() {
    const h = this.getQuizHistory();
    return h.length ? h[0] : null;
  },

  // Completed courses
  completeCourse(courseId) {
    const completed = this.getCompletedCourses();
    if (!completed.includes(courseId)) {
      completed.push(courseId);
      localStorage.setItem("completedCourses", JSON.stringify(completed));
    }
  },
  getCompletedCourses() {
    return JSON.parse(localStorage.getItem("completedCourses") || "[]");
  },
  isCourseCompleted(courseId) {
    return this.getCompletedCourses().includes(courseId);
  },

  // Learner profile
  saveProfile(profile) {
    localStorage.setItem("learnerProfile", JSON.stringify(profile));
  },
  getProfile() {
    return JSON.parse(
      localStorage.getItem("learnerProfile") ||
        JSON.stringify({
          name: "Alex Johnson",
          email: "alex@example.com",
          bio: "Passionate learner exploring web development.",
          avatar: "AJ",
        })
    );
  },
};
