export function build(): number {
    const options = {
        retries: 3,
        timeout: 100,
    };
    const total = options.retries + options.timeout;
    return total;
}
