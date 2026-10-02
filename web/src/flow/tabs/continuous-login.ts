export type ContinuousLoginExit = "now" | "suppress" | "on-pagehide";

export function continuousLoginExit(
    target: URL,
    currentOrigin: string,
    hold: boolean,
): ContinuousLoginExit {
    if (target.origin !== currentOrigin) {
        return "now";
    }

    return hold ? "suppress" : "on-pagehide";
}
