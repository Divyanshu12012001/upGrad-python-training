// quiz.js — Quiz page logic

// ── Async quiz loader using Promise + async/await + setTimeout ──
function loadQuizData() {
  return new Promise((resolve) => {
    setTimeout(() => resolve(quizQuestions), 1500);
  });
}

async function initQuiz() {
  try {
    const questions = await loadQuizData();
    renderQuiz(questions);
    document.getElementById("loadingState").style.display = "none";
    document.getElementById("quizContent").style.display = "block";
  } catch (err) {
    document.getElementById("loadingState").innerHTML =
      `<p class="text-danger">❌ Failed to load quiz. Please refresh.</p>`;
  }
}

// ── Render quiz questions dynamically ──
function renderQuiz(questions) {
  document.getElementById("questionCount").textContent =
    `${questions.length} Questions`;
  document.getElementById("quizProgress").max = questions.length;

  const container = document.getElementById("questionsContainer");
  container.innerHTML = questions
    .map(
      (q, i) => `
      <div class="question-card" id="qcard-${q.id}" role="group"
        aria-labelledby="qlabel-${q.id}">
        <div class="question-number">Question ${i + 1} of ${questions.length}</div>
        <div class="question-text" id="qlabel-${q.id}">${q.question}</div>
        <div role="radiogroup" aria-label="Options for question ${i + 1}">
          ${q.options
            .map(
              (opt, j) => `
            <label class="option-label" id="opt-${q.id}-${j}">
              <input type="radio" name="q${q.id}" value="${j}"
                onchange="onAnswerChange(${q.id})"
                aria-label="${opt}" />
              <span>${opt}</span>
            </label>`
            )
            .join("")}
        </div>
      </div>`
    )
    .join("");
}

// ── onchange event: update progress bar ──
function onAnswerChange(questionId) {
  const answered = quizQuestions.filter((q) => {
    const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
    return selected !== null;
  }).length;

  document.getElementById("answeredCount").textContent = `${answered} answered`;
  document.getElementById("quizProgress").value = answered;
}

// ── Grade calculation (if-else) ──
function calculateGrade(percentage) {
  if (percentage >= 90) return "A+";
  else if (percentage >= 80) return "A";
  else if (percentage >= 70) return "B";
  else if (percentage >= 60) return "C";
  else if (percentage >= 50) return "D";
  else return "F";
}

// ── Score percentage calculation ──
function calculatePercentage(score, total) {
  if (total === 0) return 0;
  return Math.round((score / total) * 100);
}

// ── Pass/Fail determination ──
function isPassed(percentage) {
  return percentage >= 50;
}

// ── Switch: performance feedback ──
function getPerformanceFeedback(grade) {
  switch (grade) {
    case "A+": return { msg: "Outstanding! You're a star learner! 🌟", emoji: "🏆" };
    case "A":  return { msg: "Excellent work! Keep it up! 🎉", emoji: "🥇" };
    case "B":  return { msg: "Good job! A little more practice and you'll ace it!", emoji: "👍" };
    case "C":  return { msg: "Not bad! Review the material and try again.", emoji: "📖" };
    case "D":  return { msg: "You passed, but there's room to improve.", emoji: "💪" };
    default:   return { msg: "Don't give up! Review the courses and try again.", emoji: "🔄" };
  }
}

// ── onclick: Submit quiz ──
function submitQuiz() {
  // Validate — check if all questions answered
  const unanswered = quizQuestions.filter(
    (q) => !document.querySelector(`input[name="q${q.id}"]:checked`)
  );

  if (unanswered.length > 0) {
    if (!confirm(`You have ${unanswered.length} unanswered question(s). Submit anyway?`)) {
      return;
    }
  }

  let score = 0;
  let wrong = 0;
  let skipped = 0;

  quizQuestions.forEach((q) => {
    const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
    const correctIdx = q.answer;

    // Highlight correct/incorrect options
    q.options.forEach((_, j) => {
      const label = document.getElementById(`opt-${q.id}-${j}`);
      const input = label.querySelector("input");
      input.disabled = true;

      if (j === correctIdx) {
        label.classList.add("correct");
      } else if (selected && parseInt(selected.value) === j) {
        label.classList.add("incorrect");
      }
    });

    if (!selected) {
      skipped++;
    } else if (parseInt(selected.value) === correctIdx) {
      score++;
    } else {
      wrong++;
    }
  });

  const total = quizQuestions.length;
  const percentage = calculatePercentage(score, total);
  const grade = calculateGrade(percentage);
  const passed = isPassed(percentage);
  const feedback = getPerformanceFeedback(grade);

  // Save to localStorage
  Storage.saveQuizResult({
    score,
    total,
    percentage,
    grade,
    passed,
    date: new Date().toISOString(),
  });

  // Show results
  document.getElementById("resultScore").textContent = `${percentage}%`;
  document.getElementById("resultGrade").textContent =
    `Grade: ${grade} — ${passed ? "✅ PASSED" : "❌ FAILED"}`;
  document.getElementById("resultFeedback").textContent = feedback.msg;
  document.getElementById("resultEmoji").textContent = feedback.emoji;
  document.getElementById("correctCount").textContent = score;
  document.getElementById("wrongCount").textContent = wrong;
  document.getElementById("skippedCount").textContent = skipped;

  // Hide submit button, show results
  document.getElementById("submitBtn").style.display = "none";
  document.getElementById("resultSection").style.display = "block";

  // Scroll to results
  document.getElementById("resultSection").scrollIntoView({ behavior: "smooth" });
}

// ── Retake quiz ──
function retakeQuiz() {
  document.getElementById("resultSection").style.display = "none";
  document.getElementById("submitBtn").style.display = "inline-block";
  document.getElementById("quizContent").style.display = "none";
  document.getElementById("loadingState").style.display = "flex";
  document.getElementById("answeredCount").textContent = "0 answered";
  document.getElementById("quizProgress").value = 0;
  initQuiz();
}

// ── Bootstrap ──
document.addEventListener("DOMContentLoaded", initQuiz);

// ── Export for Jest tests ──
if (typeof module !== "undefined") {
  module.exports = { calculateGrade, calculatePercentage, isPassed, getPerformanceFeedback };
}
