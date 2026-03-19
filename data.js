// Shared course and quiz data

const courses = [
  {
    id: 1,
    title: "HTML & CSS Fundamentals",
    category: "Web Development",
    duration: "4 hours",
    lessons: [
      "Introduction to HTML",
      "HTML Elements & Attributes",
      "CSS Selectors & Properties",
      "Box Model & Layout",
      "Responsive Design Basics",
    ],
    description: "Learn the building blocks of the web with HTML and CSS.",
    icon: "🌐",
  },
  {
    id: 2,
    title: "JavaScript Essentials",
    category: "Programming",
    duration: "6 hours",
    lessons: [
      "Variables & Data Types",
      "Functions & Scope",
      "DOM Manipulation",
      "Events & Listeners",
      "Async JavaScript",
    ],
    description: "Master core JavaScript concepts for modern web development.",
    icon: "⚡",
  },
  {
    id: 3,
    title: "Bootstrap Framework",
    category: "Web Development",
    duration: "3 hours",
    lessons: [
      "Grid System",
      "Components Overview",
      "Utility Classes",
      "Forms & Validation",
      "Customizing Bootstrap",
    ],
    description: "Build responsive UIs quickly using Bootstrap 5.",
    icon: "🎨",
  },
  {
    id: 4,
    title: "Python for Beginners",
    category: "Programming",
    duration: "8 hours",
    lessons: [
      "Python Syntax & Variables",
      "Control Flow",
      "Functions & Modules",
      "File Handling",
      "Introduction to OOP",
    ],
    description: "Start your programming journey with Python.",
    icon: "🐍",
  },
];

const quizQuestions = [
  {
    id: 1,
    question: "Which HTML tag is used to define an unordered list?",
    options: ["<ol>", "<ul>", "<li>", "<list>"],
    answer: 1,
  },
  {
    id: 2,
    question: "Which CSS property controls the text size?",
    options: ["font-weight", "text-size", "font-size", "text-style"],
    answer: 2,
  },
  {
    id: 3,
    question: "What does DOM stand for?",
    options: [
      "Document Object Model",
      "Data Object Management",
      "Document Oriented Model",
      "Dynamic Object Module",
    ],
    answer: 0,
  },
  {
    id: 4,
    question: "Which keyword declares a block-scoped variable in JavaScript?",
    options: ["var", "let", "define", "set"],
    answer: 1,
  },
  {
    id: 5,
    question: "What is the output of typeof null in JavaScript?",
    options: ["null", "undefined", "object", "string"],
    answer: 2,
  },
  {
    id: 6,
    question: "Which Bootstrap class creates a responsive container?",
    options: [".wrapper", ".container", ".box", ".grid"],
    answer: 1,
  },
  {
    id: 7,
    question: "Which method adds an element at the end of a JavaScript array?",
    options: ["push()", "pop()", "shift()", "append()"],
    answer: 0,
  },
  {
    id: 8,
    question: "What does CSS stand for?",
    options: [
      "Computer Style Sheets",
      "Creative Style Syntax",
      "Cascading Style Sheets",
      "Colorful Style Sheets",
    ],
    answer: 2,
  },
  {
    id: 9,
    question: "Which Python function prints output to the console?",
    options: ["echo()", "console.log()", "print()", "write()"],
    answer: 2,
  },
  {
    id: 10,
    question: "What is the correct way to write an arrow function in JavaScript?",
    options: [
      "function => () {}",
      "const fn = () => {}",
      "fn() -> {}",
      "arrow fn() {}",
    ],
    answer: 1,
  },
];

// Export for Node/Jest environment
if (typeof module !== "undefined") {
  module.exports = { courses, quizQuestions };
}
