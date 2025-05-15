declare module "*.md" {
    /**
     * The serialized JSON content of an MD file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}

declare module "*.mdx" {
    /**
     * The serialized JSON content of an MDX file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}
