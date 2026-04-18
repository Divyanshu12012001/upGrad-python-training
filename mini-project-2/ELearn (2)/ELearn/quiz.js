// quiz.js — API-connected quiz page

let currentQuestions = [];
let currentQuizId = null;

function calculateGrade(p) {
  if (p >= 90) return 'A+';
  if (p >= 80) return 'A';
  if (p >= 70) return 'B';
  if (p >= 60) return 'C';
  if (p >= 50) return 'D';
  return 'F';
}

function calculatePercentage(score, total) {
  return total === 0 ? 0 : Math.round((score / total) * 100);
}

function isPassed(p) { return p >= 50; }

function getPerformanceFeedback(grade) {
  const map = {
    'A+': { msg: "Outstanding! You're a star learner! 🌟", emoji: '🏆' },
    'A':  { msg: 'Excellent work! Keep it up! 🎉',          emoji: '🥇' },
    'B':  { msg: 'Good job! A little more practice!',       emoji: '👍' },
    'C':  { msg: 'Not bad! Review the material.',           emoji: '📖' },
    'D':  { msg: "You passed, but there's room to improve.",emoji: '💪' },
  };
  return map[grade] || { msg: "Don't give up! Review and try again.", emoji: '🔄' };
}

async function initQuiz() {
  if (Auth.redirectIfNotLoggedIn()) return;
  document.getElementById('loadingState').style.display = 'flex';
  document.getElementById('quizContent').style.display = 'none';

  try {
    // Read courseId from URL param, default to first quiz
    const params = new URLSearchParams(window.location.search);
    const courseId = params.get('courseId') || '1';

    const quizzes = await Api.get(`/quizzes/by-course/${courseId}`);
    if (!quizzes.length) throw new Error('No quizzes for this course.');

    currentQuizId = quizzes[0].quizId;
    currentQuestions = await Api.get(`/quizzes/${currentQuizId}/questions`);

    if (!currentQuestions.length) throw new Error('No questions found.');

    document.getElementById('questionCount').textContent = `${currentQuestions.length} Questions`;
    document.getElementById('quizProgress').max = currentQuestions.length;

    document.getElementById('questionsContainer').innerHTML = currentQuestions.map((q, i) => `
      <div class="question-card" id="qcard-${q.questionId}">
        <div class="question-number">Question ${i + 1} of ${currentQuestions.length}</div>
        <div class="question-text">${q.questionText}</div>
        <div>
          ${['A', 'B', 'C', 'D'].map((opt, j) => `
            <label class="option-label" id="opt-${q.questionId}-${opt}">
              <input type="radio" name="q${q.questionId}" value="${opt}"
                onchange="onAnswerChange()" aria-label="${q['option' + opt]}" />
              <span>${q['option' + opt]}</span>
            </label>`).join('')}
        </div>
      </div>`).join('');

    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('quizContent').style.display = 'block';
  } catch (err) {
    document.getElementById('loadingState').innerHTML =
      `<p class="text-danger">❌ ${err.message} Ensure the API is running.</p>`;
  }
}

function onAnswerChange() {
  const answered = currentQuestions.filter(q =>
    document.querySelector(`input[name="q${q.questionId}"]:checked`)).length;
  document.getElementById('answeredCount').textContent = `${answered} answered`;
  document.getElementById('quizProgress').value = answered;
}

async function submitQuiz() {
  const unanswered = currentQuestions.filter(q =>
    !document.querySelector(`input[name="q${q.questionId}"]:checked`));
  if (unanswered.length > 0 && !confirm(`${unanswered.length} unanswered question(s). Submit anyway?`)) return;

  // Highlight answers
  let correct = 0, wrong = 0, skipped = 0;
  currentQuestions.forEach(q => {
    const selected = document.querySelector(`input[name="q${q.questionId}"]:checked`);
    ['A', 'B', 'C', 'D'].forEach(opt => {
      const label = document.getElementById(`opt-${q.questionId}-${opt}`);
      label.querySelector('input').disabled = true;
      if (opt === q.correctAnswer) label.classList.add('correct');
      else if (selected?.value === opt) label.classList.add('incorrect');
    });
    if (!selected) skipped++;
    else if (selected.value === q.correctAnswer) correct++;
    else wrong++;
  });

  // Submit to API
  try {
    const answers = currentQuestions.map(q => ({
      questionId: q.questionId,
      selectedAnswer: document.querySelector(`input[name="q${q.questionId}"]:checked`)?.value || ''
    })).filter(a => a.selectedAnswer);

    const result = await Api.post(`/quizzes/${currentQuizId}/submit`, {
      userId: Auth.getUserId(),
      answers
    });

    document.getElementById('resultScore').textContent = `${result.percentage}%`;
    document.getElementById('resultGrade').textContent =
      `Grade: ${result.grade} — ${result.passed ? '✅ PASSED' : '❌ FAILED'}`;
    const fb = getPerformanceFeedback(result.grade);
    document.getElementById('resultFeedback').textContent = fb.msg;
    document.getElementById('resultEmoji').textContent = fb.emoji;
    document.getElementById('correctCount').textContent = correct;
    document.getElementById('wrongCount').textContent = wrong;
    document.getElementById('skippedCount').textContent = skipped;
    document.getElementById('submitBtn').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert('Failed to submit quiz. Please try again.');
  }
}

function retakeQuiz() {
  document.getElementById('resultSection').style.display = 'none';
  document.getElementById('submitBtn').style.display = 'inline-block';
  document.getElementById('answeredCount').textContent = '0 answered';
  document.getElementById('quizProgress').value = 0;
  initQuiz();
}

document.addEventListener('DOMContentLoaded', initQuiz);

if (typeof module !== 'undefined') {
  module.exports = { calculateGrade, calculatePercentage, isPassed, getPerformanceFeedback };
}
