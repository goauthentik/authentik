/**
 * @file Provides types for ESBuild "virtual modules" generated from MDX files.
 */

declare module "~docs/types" {
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
}

declare module "~docs/*.md" {
    /**
     * The serialized JSON content of an MD file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}

declare module "~docs/*.mdx" {
    /**
     * The serialized JSON content of an MDX file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}
