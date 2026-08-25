/**
 * @file Provides types for ESBuild "virtual modules" generated from
 * Markdown / MDX files. The bundler's `mdx-plugin` compiles these to
 * HTML at build time and emits a JSON envelope; importing the file
 * yields the URL of that JSON envelope.
 */

declare module "~docs/*.md" {
    /**
     * URL of the JSON envelope emitted for the imported file.
     */
    const url: string;
    export default url;
}

declare module "~docs/*.mdx" {
    /**
     * URL of the JSON envelope emitted for the imported file.
     */
    const url: string;
    export default url;
}
