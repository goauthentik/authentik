/**
 * @file ESLint rule to enforce the use of the `node:` prefix for Node.js built-in modules.
 *
 * @import { Rule, ESLint } from "eslint";
 * @import { RuleTextEditor } from "@eslint/core";
 */
import { builtinModules } from "node:module";

const NODE_PROTOCOL_PREFIX = "node:";

/**
 * @type {Map<string, string>}
 */
const NodeModulesIndex = new Map();

for (const moduleName of builtinModules) {
    if (moduleName.startsWith("_")) continue;
    if (moduleName.startsWith(NODE_PROTOCOL_PREFIX)) continue;

    NodeModulesIndex.set(moduleName, `${NODE_PROTOCOL_PREFIX}${moduleName}`);
}

/**
 * @type {Rule.RuleModule}
 */
const rule = {
    meta: {
        type: "problem",
        fixable: "code",
        hasSuggestions: true,
        docs: {
            description: "Enforce `node:` prefix for Node.js built-in modules.",
            recommended: true,
        },
    },
    create: (context) => {
        /**
         * @type {Rule.RuleListener}
         */
        const ruleListener = {
            ImportDeclaration({ source }) {
                if (source.type !== "Literal" || typeof source.value !== "string") {
                    return;
                }

                const moduleName = source.value;

                const prefixedModuleName = NodeModulesIndex.get(moduleName);

                if (!prefixedModuleName) return;

                /**
                 * @param {RuleTextEditor} editor
                 */
                const fix = (editor) =>
                    editor.replaceText(source, JSON.stringify(prefixedModuleName));

                context.report({
                    node: source,
                    message: `Module "${moduleName}" must use the "node:" prefix.`,
                    fix,
                    suggest: [
                        {
                            fix,
                            desc: `Use "${prefixedModuleName}" instead.`,
                        },
                    ],
                });
            },
        };

        return ruleListener;
    },
};

/**
 * @type {ESLint.Plugin}
 */
const NodeLintPlugin = {
    rules: {
        "no-unprefixed-imports": rule,
    },
};

export default NodeLintPlugin;
