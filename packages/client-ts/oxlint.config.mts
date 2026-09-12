export default {
    plugins: ["typescript"],
    categories: {},
    rules: { "no-unused-vars": ["warn", { args: "none", varsIgnorePattern: "^_" }] },
    ignorePatterns: ["**/node_modules", "**/dist", "**/out", "docs/**"],
};
