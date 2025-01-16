/**
 * Add support GFM (autolink literals, footnotes, strikethrough, tables,
 * tasklists).
 *
 * @param {Options | null | undefined} [options]
 *   Configuration (optional).
 * @returns {undefined}
 *   Nothing.
 */
export default function remarkGfm(options?: Options | null | undefined): undefined;
export type Root = import('mdast').Root;
export type MdastOptions = import('mdast-util-gfm').Options;
export type MicromarkOptions = import('micromark-extension-gfm').Options;
export type Processor = import('unified').Processor<Root>;
/**
 * Configuration.
 */
export type Options = MicromarkOptions & MdastOptions;
