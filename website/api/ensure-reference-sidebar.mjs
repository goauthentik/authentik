import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
try {
    require.resolve("#reference/sidebar");
} catch (_error) {
    console.error(
        "\n⛔️ API Reference sidebar not found.\n\nRun `npm run build:api` to generate files.",
    );
    process.exit(1);
}
