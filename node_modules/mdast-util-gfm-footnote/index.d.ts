export {gfmFootnoteFromMarkdown, gfmFootnoteToMarkdown} from './lib/index.js'

declare module 'mdast-util-to-markdown' {
  interface ConstructNameMap {
    /**
     * Footnote reference.
     *
     * ```markdown
     * > | A[^b].
     *      ^^^^
     * ```
     */
    footnoteReference: 'footnoteReference'

    /**
     * Footnote definition.
     *
     * ```markdown
     * > | [^a]: B.
     *     ^^^^^^^^
     * ```
     */
    footnoteDefinition: 'footnoteDefinition'
  }
}
