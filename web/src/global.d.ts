declare module "*.css";

declare module "*.md" {
    const html: string;
    const metadata: { [key: string]: string };
    const filename: string;
}

declare namespace Intl {
    class ListFormat {
        constructor(locale: string, args: { [key: string]: string });
        public format: (items: string[]) => string;
    }
}

declare interface Window {
    authentik_sdk?: {
        base: string;
        token?: string;
        forceTheme?: string;
    };
}
