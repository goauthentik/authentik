export function report(label: string): string {
    const prefix = label.trim();
    console.info(prefix);
    console.warn(prefix);
    const suffix = prefix.toUpperCase();
    return suffix;
}
