/**
 * @remarks
 *   An iframe inside a multi-line template is reported on its own line, which a disable-next-line
 *   comment above the template does not reach. Wrap the template in a block comment pair instead:
 *   `oxlint-disable goauthentik/iframe-sandbox` before it and `oxlint-enable` after it, with the
 *   reason in a comment above.
 * @file The `goauthentik/iframe-sandbox` rule: every `<iframe>` in a lit-html template has a static
 *   `sandbox` attribute, and the attribute does not pair `allow-scripts` with `allow-same-origin`.
 *   Without a sandbox, a document in `srcdoc` or a `javascript:` URL in `src` runs in this page's
 *   origin, with full access to the page. With both tokens, same-origin content can remove its own
 *   sandbox. The rule cannot check an iframe made through the DOM API, or a `srcdoc` set through
 *   it, so it reports those for a suppression that states why they are safe.
 */

import type { AstNode, Rule } from "./plugin-types.js";

import { TemplateAnalyzer } from "eslint-plugin-lit/lib/template-analyzer.js";

/** The attribute and Lit bindings that set the sandbox. */
const SANDBOX_BINDINGS = new Set(["sandbox", "?sandbox", ".sandbox"]);

/** The attribute and Lit binding that set the frame's document. */
const SRCDOC_BINDINGS = new Set(["srcdoc", ".srcdoc"]);

const Messages = {
    missing:
        '<iframe> without a sandbox attribute. Start from sandbox="" and add only the allow-* tokens the framed page needs.',
    srcdoc: '<iframe srcdoc> without a sandbox runs the document in this page\'s origin. Add sandbox="".',
    bound: "The iframe sandbox must be a static attribute, so its tokens can be checked.",
    escape: "sandbox with both allow-scripts and allow-same-origin lets same-origin content remove its own sandbox.",
    domIframe:
        "An iframe made with the DOM API cannot be checked for a sandbox. Render it in a lit-html template, or suppress this with the reason it is safe.",
    domSrcdoc:
        "srcdoc set through the DOM API cannot be checked for a sandbox. Bind it in a lit-html template, or suppress this with the reason it is safe.",
} as const;

type AnalyzedNode = Parameters<typeof TemplateAnalyzer.create>[0];
type AnalyzerSource = Parameters<TemplateAnalyzer["resolveLocation"]>[1];

/**
 * The value of a string literal.
 *
 * @param node The node to read.
 *
 * @returns The string, or `null` for anything else.
 */
function stringValue(node: AstNode | undefined): string | null {
    return node?.type === "Literal" && typeof node.value === "string" ? node.value : null;
}

export const iframeSandboxRule: Rule = {
    meta: {
        name: "iframe-sandbox",
        type: "problem",
        schema: [],
    },
    create(context) {
        const sourceCode = context.sourceCode ?? context.getSourceCode!();
        // eslint-plugin-lit types its analyzer against ESLint's ESTree and SourceCode. oxlint hands
        // rules objects of the same shape, so the bundled rules' loose types cross over here.
        const source = sourceCode as unknown as AnalyzerSource;

        return {
            TaggedTemplateExpression(node: AstNode) {
                if (node.tag?.type !== "Identifier" || node.tag.name !== "html") return;

                const analyzer = TemplateAnalyzer.create(node as unknown as AnalyzedNode);

                analyzer.traverse({
                    enterElement(element) {
                        if (element.name !== "iframe") return;

                        const startTag = element.sourceCodeLocation?.startTag;
                        const loc = startTag ? analyzer.resolveLocation(startTag, source) : null;
                        const report = (message: string) =>
                            context.report({ node, ...(loc && { loc }), message });

                        const names = Object.keys(element.attribs);
                        const sandbox = names.find((name) => SANDBOX_BINDINGS.has(name));

                        if (!sandbox) {
                            const hasSrcdoc = names.some((name) => SRCDOC_BINDINGS.has(name));

                            report(hasSrcdoc ? Messages.srcdoc : Messages.missing);

                            return;
                        }

                        // A property or boolean binding is never static; an attribute value is
                        // static unless the analyzer finds an expression inside it.
                        const value =
                            sandbox === "sandbox"
                                ? analyzer.getAttributeValue(element, sandbox, source)
                                : null;

                        if (typeof value !== "string") {
                            report(Messages.bound);

                            return;
                        }

                        const tokens = new Set(value.toLowerCase().split(/\s+/));

                        if (tokens.has("allow-scripts") && tokens.has("allow-same-origin")) {
                            report(Messages.escape);
                        }
                    },
                });
            },

            CallExpression(node: AstNode) {
                const callee = node.callee;

                if (callee?.type !== "MemberExpression" || callee.computed) return;

                const method = callee.property?.name;
                const name = stringValue(node.arguments?.[0])?.toLowerCase();

                if (method === "createElement" && name === "iframe") {
                    context.report({ node, message: Messages.domIframe });
                } else if (method === "setAttribute" && name === "srcdoc") {
                    context.report({ node, message: Messages.domSrcdoc });
                }
            },

            AssignmentExpression(node: AstNode) {
                const left = node.left;

                if (
                    left?.type === "MemberExpression" &&
                    !left.computed &&
                    left.property?.name === "srcdoc"
                ) {
                    context.report({ node, message: Messages.domSrcdoc });
                }
            },
        };
    },
};

export default iframeSandboxRule;
