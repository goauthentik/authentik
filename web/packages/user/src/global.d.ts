declare module "*.css";

declare module "*.md" {
    const html: string;
    const metadata: { [key: string]: string };
    const filename: string;
}
