/**
 * Create an extension for `mdast-util-from-markdown` to enable directives in
 * markdown.
 *
 * @returns {FromMarkdownExtension}
 *   Extension for `mdast-util-from-markdown` to enable directives.
 */
export function directiveFromMarkdown(): FromMarkdownExtension
/**
 * Create an extension for `mdast-util-to-markdown` to enable directives in
 * markdown.
 *
 * @returns {ToMarkdownExtension}
 *   Extension for `mdast-util-to-markdown` to enable directives.
 */
export function directiveToMarkdown(): ToMarkdownExtension
export type Nodes = import('mdast').Nodes
export type Paragraph = import('mdast').Paragraph
export type CompileContext = import('mdast-util-from-markdown').CompileContext
export type FromMarkdownExtension = import('mdast-util-from-markdown').Extension
export type FromMarkdownHandle = import('mdast-util-from-markdown').Handle
export type Token = import('mdast-util-from-markdown').Token
export type ConstructName = import('mdast-util-to-markdown').ConstructName
export type ToMarkdownHandle = import('mdast-util-to-markdown').Handle
export type ToMarkdownExtension = import('mdast-util-to-markdown').Options
export type State = import('mdast-util-to-markdown').State
export type Directives = import('../index.js').Directives
export type LeafDirective = import('../index.js').LeafDirective
export type TextDirective = import('../index.js').TextDirective
