export function pathEnders(values: number[]): number {
    let total = 0;
    for (const value of values) {
        if (value < 0) continue;
        total += value;
        total++;
    }
    return total;
}
