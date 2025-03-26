import { createContext, useContext } from "react";

/**
 * A parsed JSON module containing MDX content and metadata from ESBuild.
 */
export interface MDXModule {
    /**
     * The Markdown content of the module.
     */
    content: string;
    /**
     * The public path of the module, typically identical to the docs page path.
     */
    publicPath?: string;
    /**
     * The public directory of the module, used to resolve relative links.
     */
    publicDirectory?: string;
}

/**
 * Fetches an MDX module from a URL or ESBuild static asset.
 */
export function fetchMDXModule(url: string | URL): Promise<MDXModule> {
    return fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch content: ${response.statusText}`);
            }

            return response.json();
        })
        .catch((error) => {
            console.error("Error fetching content", error);
            return { content: "", publicPath: "", publicDirectory: "" };
        });
}

/**
 * A context for the current MDX module.
 */
export const MDXModuleContext = createContext<MDXModule>({
    content: "",
});

MDXModuleContext.displayName = "MDXModuleContext";

/**
 * A hook to access the current MDX module.
 */
export function useMDXModule(): MDXModule {
    return useContext(MDXModuleContext);
}
