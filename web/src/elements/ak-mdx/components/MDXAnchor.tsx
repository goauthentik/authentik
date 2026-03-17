import { useMDXModule } from "#elements/ak-mdx/MDXModuleContext";

import React from "react";

/**
 * A simplified version of Node's `path.resolve`:
 */
function resolvePath(...args: string[]): string {
    const pathname = args
        // Combine all arguments into a single path...
        .join("/")
        // Normalizing any delimiting slashes...
        .replace(/\/{2,}/g, "/");

    return new URL(pathname, "file:///").pathname;
}

/**
 * A custom anchor element that applies special behavior for MDX content.
 *
 * - Resolves relative links to the public directory in the public docs domain.
 * - Intercepts local links and scrolls to the target element.
 */
export const MDXAnchor = ({
    href,
    children,
    ...props
}: React.AnchorHTMLAttributes<HTMLAnchorElement>) => {
    const { publicDirectory } = useMDXModule();

    if (href?.startsWith(".") && publicDirectory) {
        const nextPathname = resolvePath(publicDirectory, href);

        const nextURL = new URL(nextPathname, import.meta.env.AK_DOCS_URL);
        // Remove trailing .md and .mdx, and trailing "index".
        nextURL.pathname = nextURL.pathname.replace(/(index)?\.mdx?$/, "");
        href = nextURL.toString();
    }

    const interceptHeadingLinks = (event: React.MouseEvent<HTMLAnchorElement>) => {
        if (!href || !href.startsWith("#")) return;

        event.preventDefault();

        const rootNode = event.currentTarget.getRootNode() as ShadowRoot;

        const elementID = href.slice(1);
        const target = rootNode.getElementById(elementID);

        if (!target) {
            console.warn(`Element with ID ${elementID} not found`);
            return;
        }

        target.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    };

    return (
        <a
            href={href}
            onClick={interceptHeadingLinks}
            rel="noopener noreferrer"
            target="_blank"
            {...props}
        >
            {children}
        </a>
    );
};
