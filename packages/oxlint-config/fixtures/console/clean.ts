export function report(label: string): string {
    console.info("starting");
    console.warn("still starting");

    const prefix = label.trim();

    console.info(prefix);
}
