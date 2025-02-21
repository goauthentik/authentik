import { useDoc } from "@docusaurus/plugin-content-docs/client";

/**
 * Title can be declared inside md content or declared through
 * front matter and added manually. To make both cases consistent,
 * the added title is added under the same div.markdown block
 * See https://github.com/facebook/docusaurus/pull/4882#issuecomment-853021120
 *
 * We render a "synthetic title" if:
 * - user doesn't ask to hide it with front matter
 * - the markdown content does not already contain a top-level h1 heading
 *
 * @vendor docusaurus
 */
export function useSyntheticTitle(): string | null {
    const { metadata, frontMatter, contentTitle } = useDoc();
    const shouldRender =
        !frontMatter.hide_title && typeof contentTitle === "undefined";
    if (!shouldRender) {
        return null;
    }
    return metadata.title;
}
