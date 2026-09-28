import js from "@eslint/js";
import globals from "globals";
export default [
  js.configs.recommended,
  {
    files: ["src/web/static/**/*.js"],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "script",
      globals: globals.browser,
    },
    rules: {
      "no-unused-vars": ["error", { caughtErrors: "none" }],
      eqeqeq: "error",
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
    },
  },
];
