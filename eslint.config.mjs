import js from "@eslint/js";
import html from "eslint-plugin-html";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["**/*.html", "**/*.js"],
    plugins: {
      html
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: {
        ...globals.browser,
        L: "readonly",
        google: "readonly",
      }
    },
    rules: {
      "no-undef": "error",
      "no-use-before-define": ["error", { "functions": false, "classes": true, "variables": true }],
      "no-unused-vars": ["error", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_", "caughtErrorsIgnorePattern": "^_" }],
      "no-unreachable": "error",
      "no-constant-condition": "error",
      "no-dupe-keys": "error",
      "no-duplicate-case": "error",
      "no-func-assign": "error",
      "no-invalid-regexp": "error",
      "no-irregular-whitespace": "error",
      "no-obj-calls": "error",
      "no-sparse-arrays": "error",
      "no-unexpected-multiline": "error",
      "use-isnan": "error",
      "valid-typeof": "error"
    }
  }
];
