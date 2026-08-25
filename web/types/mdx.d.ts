/**
<<<<<<< HEAD
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

=======
 * @file Provides types for ESBuild "virtual modules" generated from
 * MDX files. The bundler's `mdx-plugin` compiles these to
 * HTML at build time and emits a JSON envelope; importing the file
 * yields the URL of that JSON envelope.
 */

>>>>>>> 15aa5e86a (website: mdx (#25246))
declare module "~docs/*.mdx" {
    /**
     * The serialized JSON content of an MDX file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}
