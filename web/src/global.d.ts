declare module "*.css";

declare module "*.md" {
    /**
     * The HTML content of the markdown file.
     */
    const html: string;
    export default html;
}

declare module "*.mdx" {
    /**
     * The HTML content of the markdown file.
     */
    const html: string;
    export default html;
}

declare namespace Intl {
    class ListFormat {
        constructor(locale: string, args: { [key: string]: string });
        public format: (items: string[]) => string;
    }
}
