// eslint.config.js
module.exports = [
  {
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "warn",
      "padding-line-between-statements": [
        "warn",
        { blankLine: "always", prev: "*", next: "function" },
        { blankLine: "always", prev: "function", next: "*" },
        { blankLine: "always", prev: "*", next: "class" },
        { blankLine: "always", prev: "class", next: "*" },
      ],
    },
  },
];
