/**
 * Client-side cooldown for "resend code" buttons.
 *
 * This only drives the UI. The server applies the same window per email address, so a client that
 * skips the countdown still cannot use the resend endpoint to mail-bomb an address.
 */
export const RESEND_COOLDOWN_SECONDS = 60;

/**
 * Count `seconds` down to zero, calling `onTick` immediately and once per second after that.
 * Returns a function that cancels the countdown.
 */
export function startResendCooldown(
    seconds: number,
    onTick: (remaining: number) => void,
): () => void {
    let remaining = seconds;

    onTick(remaining);

    const timer = setInterval(() => {
        remaining -= 1;
        onTick(Math.max(remaining, 0));

        if (remaining <= 0) {
            clearInterval(timer);
        }
    }, 1000);

    return () => clearInterval(timer);
}
