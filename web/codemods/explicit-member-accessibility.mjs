/* eslint-disable max-depth */
/**
 * @file TypeScript codemod to add explicit member accessibility modifiers to class methods and properties.
 *
 * Given a class like this:
 *
 * ```ts
 * class Foo {
 *     static styles = [
 *       css`
 *         :host {
 *           display: block;
 *         }
 *       `,
 *     ];
 *
 *     @property()
 *     name?: string;
 *
 *     @state()
 *     isLoading = false;
 *
 *     renderHeader() {
 *         return html`<h1>Hello world</h1>`;
 *     }
 *
 *     render() {
 *         return html`
 *           ${this.renderHeader()}
 *           <div>Content</div>
 *         `;
 *     }
 * }
 * ```
 *
 * This codemod will transform it to this:
 *
 * ```ts
 * class Foo {
 *     public static styles = [
 *       css`
 *         :host {
 *           display: block;
 *         }
 *       `,
 *     ];
 *
 *     @property()
 *     public name?: string;
 *
 *     @state()
 *     protected isLoading = false;
 *
 *     protected renderHeader() {
 *         return html`<h1>Hello world</h1>`;
 *     }
 *
 *     public render() {
 *         return html`
 *           ${this.renderHeader()}
 *           <div>Content</div>
 *         `;
 *     }
 * }
 * ```
 *
 * Rules:
 * - Any method which is `render` is given an explicit `public` accessibility modifier.
 * - Any method which begins with `render` is given an explicit `protected` accessibility modifier.
 * - Any property which is static is given an explicit `public` accessibility modifier.
 * - Any property with `@property` decorator is given an explicit `public` accessibility modifier.
 * - Any property with `@state` decorator is given an explicit `protected` accessibility modifier.
 * - Methods and properties which already have an accessibility modifier are left alone.
 * - Private fields (starting with #) are skipped.
 */

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import ts from "typescript";

/**
 * @param {ts.NodeArray<ts.ModifierLike>} modifiers
 */
function hasAccessibilityModifier(modifiers) {
    if (!modifiers) return false;

    return modifiers.some(
        (modifier) =>
            modifier.kind === ts.SyntaxKind.PublicKeyword ||
            modifier.kind === ts.SyntaxKind.PrivateKeyword ||
            modifier.kind === ts.SyntaxKind.ProtectedKeyword,
    );
}

/**
 *
 * @param {ts.NodeArray<ts.ModifierLike>} [modifiers]
 * @returns
 */
function hasStaticModifier(modifiers) {
    if (!modifiers) return false;
    return modifiers.some((modifier) => modifier.kind === ts.SyntaxKind.StaticKeyword);
}

/**
 * Check if a property has a decorator.
 * @param {ts.PropertyDeclaration} member
 * @returns {boolean}
 */
function isDecorated(member) {
    if (!member.modifiers) return false;

    return member.modifiers.some((modifier) => {
        if (!ts.isDecorator(modifier)) return false;

        // Handle simple decorator like @property
        if (ts.isIdentifier(modifier.expression)) {
            return true;
        }

        // Handle decorator with call like @property() or @property({...})
        return (
            ts.isCallExpression(modifier.expression) &&
            ts.isIdentifier(modifier.expression.expression)
        );
    });
}

/**
 * Check if a property has a specific decorator
 * @param {ts.PropertyDeclaration} member
 * @param {string} decoratorName
 * @returns {boolean}
 */
function hasDecorator(member, decoratorName) {
    if (!member.modifiers) return false;

    return member.modifiers.some((modifier) => {
        if (!ts.isDecorator(modifier)) return false;

        // Handle simple decorator like @property
        if (ts.isIdentifier(modifier.expression)) {
            return modifier.expression.text === decoratorName;
        }

        // Handle decorator with call like @property() or @property({...})
        if (
            ts.isCallExpression(modifier.expression) &&
            ts.isIdentifier(modifier.expression.expression)
        ) {
            return modifier.expression.expression.text === decoratorName;
        }

        return false;
    });
}

const PublicMethodNames = new Set([
    "render",
    "connectedCallback",
    "disconnectedCallback",
    "firstUpdated",
    "updated",
    "requestUpdate",
    "willUpdate",
    "performUpdate",
    "adoptedCallback",
    "attributeChangedCallback",
]);

/**
 *
 * @param {string} filePath
 * @returns {boolean}
 */
function processFile(filePath) {
    const source = readFileSync(filePath, "utf-8");
    const sourceFile = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true);

    /**
     * @type {{ pos: number; text: string; }[]}
     */
    const changes = [];

    /**
     * @param {ts.Node} node
     */
    function collectChanges(node) {
        if (ts.isClassDeclaration(node)) {
            for (const member of node.members) {
                if (ts.isMethodDeclaration(member) || ts.isPropertyDeclaration(member)) {
                    if (member.modifiers && hasAccessibilityModifier(member.modifiers)) {
                        continue; // Already has accessibility modifier
                    }

                    let accessibilityKeyword = null;

                    if (
                        ts.isMethodDeclaration(member) &&
                        member.name &&
                        ts.isIdentifier(member.name)
                    ) {
                        const methodName = member.name.text;

                        if (PublicMethodNames.has(methodName)) {
                            accessibilityKeyword = "public ";
                        } else if (
                            methodName.startsWith("render") ||
                            methodName.startsWith("on") ||
                            methodName.startsWith("handle") ||
                            methodName.includes("Handler")
                        ) {
                            accessibilityKeyword = "protected ";
                        }
                    } else if (ts.isPropertyDeclaration(member)) {
                        // Skip private fields (starting with #)
                        if (member.name.getText().includes("#")) {
                            continue;
                        }

                        // Static properties get public modifier
                        if (hasStaticModifier(member.modifiers)) {
                            accessibilityKeyword = "public ";
                        }
                        // Properties with @property decorator get public modifier
                        else if (hasDecorator(member, "property")) {
                            accessibilityKeyword = "public ";
                        }
                        // Properties with @state decorator get protected modifier
                        else if (hasDecorator(member, "state")) {
                            accessibilityKeyword = "protected ";
                        } else if (isDecorated(member)) {
                            accessibilityKeyword = "protected ";
                        }
                    }

                    if (accessibilityKeyword) {
                        // Find the position where we should insert the accessibility modifier
                        // For properties with decorators, we need to insert after the decorators
                        let insertPos = member.getStart(sourceFile);

                        // If the member has decorators, find the position after the last decorator
                        if (
                            member.modifiers &&
                            member.modifiers.some((modifier) => ts.isDecorator(modifier))
                        ) {
                            const decorators = member.modifiers.filter((modifier) =>
                                ts.isDecorator(modifier),
                            );
                            const lastDecorator = decorators[decorators.length - 1];
                            insertPos = lastDecorator.getEnd();

                            // Find the next non-whitespace character position
                            const sourceText = sourceFile.getFullText();
                            while (
                                insertPos < sourceText.length &&
                                /\s/.test(sourceText[insertPos])
                            ) {
                                insertPos++;
                            }
                        }

                        changes.push({
                            pos: insertPos,
                            text: accessibilityKeyword,
                        });
                    }
                }
            }
        }

        ts.forEachChild(node, collectChanges);
    }

    collectChanges(sourceFile);

    if (changes.length === 0) {
        return false;
    }

    // Sort changes by position in reverse order so we can apply them without affecting positions
    changes.sort((a, b) => b.pos - a.pos);

    let result = source;
    for (const change of changes) {
        result = result.slice(0, change.pos) + change.text + result.slice(change.pos);
    }

    writeFileSync(filePath, result, "utf-8");
    // eslint-disable-next-line no-console
    console.log(`Updated: ${filePath}`);
    return true;
}

/**
 *
 * @param {string} dir
 * @param {string[]} files
 * @returns {string[]}
 */
function findTypeScriptFiles(dir = "src", files = []) {
    const entries = readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            findTypeScriptFiles(fullPath, files);
        } else if (
            entry.name.endsWith(".ts") &&
            !entry.name.endsWith(".d.ts") &&
            !entry.name.endsWith(".test.ts") &&
            !entry.name.endsWith(".spec.ts") &&
            !entry.name.endsWith(".stories.ts")
        ) {
            files.push(fullPath);
        }
    }

    return files;
}

function main() {
    const files = findTypeScriptFiles();
    let changedFiles = 0;

    for (const file of files) {
        if (processFile(file)) {
            changedFiles++;
        }
    }

    // eslint-disable-next-line no-console
    console.log(`Processed ${files.length} files, updated ${changedFiles} files`);
}

main();
