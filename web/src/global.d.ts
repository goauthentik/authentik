declare module "*.css";

declare namespace Intl {
    class ListFormat {
        constructor(locale: string, args: { [key: string]: string });
        public format: (items: string[]) => string;
    }
}
