// quiz.test.js — Jest unit tests for quiz logic

const { calculateGrade, calculatePercentage, isPassed, getPerformanceFeedback } = require("./quiz.js");

// ── 1. Grade Calculation Tests ──
describe("calculateGrade", () => {
  test("returns A+ for 90 and above", () => {
    expect(calculateGrade(90)).toBe("A+");
    expect(calculateGrade(100)).toBe("A+");
  });

  test("returns A for 80–89", () => {
    expect(calculateGrade(80)).toBe("A");
    expect(calculateGrade(85)).toBe("A");
  });

  test("returns B for 70–79", () => {
    expect(calculateGrade(70)).toBe("B");
    expect(calculateGrade(75)).toBe("B");
  });

  test("returns C for 60–69", () => {
    expect(calculateGrade(60)).toBe("C");
    expect(calculateGrade(65)).toBe("C");
  });

  test("returns D for 50–59", () => {
    expect(calculateGrade(50)).toBe("D");
    expect(calculateGrade(55)).toBe("D");
  });

  test("returns F for below 50", () => {
    expect(calculateGrade(49)).toBe("F");
    expect(calculateGrade(0)).toBe("F");
  });
});

// ── 2. Score Percentage Calculation Tests ──
describe("calculatePercentage", () => {
  test("calculates correct percentage", () => {
    expect(calculatePercentage(8, 10)).toBe(80);
    expect(calculatePercentage(10, 10)).toBe(100);
    expect(calculatePercentage(0, 10)).toBe(0);
  });

  test("rounds to nearest integer", () => {
    expect(calculatePercentage(1, 3)).toBe(33);
    expect(calculatePercentage(2, 3)).toBe(67);
  });

  test("returns 0 when total is 0 (no division by zero)", () => {
    expect(calculatePercentage(0, 0)).toBe(0);
  });
});

// ── 3. Pass/Fail Determination Tests ──
describe("isPassed", () => {
  test("returns true for percentage >= 50", () => {
    expect(isPassed(50)).toBe(true);
    expect(isPassed(75)).toBe(true);
    expect(isPassed(100)).toBe(true);
  });

  test("returns false for percentage < 50", () => {
    expect(isPassed(49)).toBe(false);
    expect(isPassed(0)).toBe(false);
  });

  test("boundary: exactly 50 is a pass", () => {
    expect(isPassed(50)).toBe(true);
  });
});

// ── 4. Performance Feedback Tests ──
describe("getPerformanceFeedback", () => {
  test("returns correct emoji and message for A+", () => {
    const result = getPerformanceFeedback("A+");
    expect(result.emoji).toBe("🏆");
    expect(result.msg).toContain("Outstanding");
  });

  test("returns fallback for F grade", () => {
    const result = getPerformanceFeedback("F");
    expect(result.emoji).toBe("🔄");
    expect(result.msg).toContain("give up");
  });

  test("returns correct feedback for B grade", () => {
    const result = getPerformanceFeedback("B");
    expect(result.emoji).toBe("👍");
  });
});
