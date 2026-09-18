export function shouldReleaseContinuousLogin(
    target: URL,
    currentOrigin: string,
    hold: boolean,
): boolean {
    return target.origin !== currentOrigin || !hold;
}
