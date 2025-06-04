/**
 * @file Temporal utilitie for working with dates and times.
 */

/**
 * Duration in milliseconds for time units used by the `Intl.RelativeTimeFormat` API.
 */
export const Duration = {
    /**
     * The number of milliseconds in a year.
     */
    year: 1000 * 60 * 60 * 24 * 365,
    /**
     * The number of milliseconds in a month.
     */
    month: (24 * 60 * 60 * 1000 * 365) / 12,
    /**
     * The number of milliseconds in a day.
     */
    day: 1000 * 60 * 60 * 24,
    /**
     * The number of milliseconds in an hour.
     */
    hour: 1000 * 60 * 60,
    /**
     * The number of milliseconds in a minute.
     */
    minute: 1000 * 60,
    /**
     * The number of milliseconds in a second.
     */
    second: 1000,
} as const satisfies Partial<Record<Intl.RelativeTimeFormatUnit, number>>;

export type DurationUnit = keyof typeof Duration;

/**
 * The order of time units used by the `Intl.RelativeTimeFormat` API.
 */
const DurationGranularity = [
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
] as const satisfies DurationUnit[];

/**
 * Given two dates, return a human-readable string describing the time elapsed between them.
 */
export function formatElapsedTime(d1: Date, d2: Date = new Date()): string {
    const elapsed = d1.getTime() - d2.getTime();
    const rtf = new Intl.RelativeTimeFormat("default", { numeric: "auto" });

    for (const unit of DurationGranularity) {
        const duration = Duration[unit];

        if (Math.abs(elapsed) > duration || unit === "second") {
            let rounded = Math.round(elapsed / duration);

            if (!isFinite(rounded)) {
                rounded = 0;
            }

            return rtf.format(rounded, unit);
        }
    }
    return rtf.format(Math.round(elapsed / 1000), "second");
}

/**
 * Convert a Date object to a string in the format required by the datetime-local input field.
 *
 * ```js
 *  html`<input
 *     type="datetime-local"
 *     data-type="datetime-local"
 *     class="pf-c-form-control"
 *     required
 *     value="${dateTimeLocal(new Date())}"
 *   />
 * ```
 *
 * @param input - The Date object to convert.
 * @returns A string in the format "YYYY-MM-DDTHH:MM" (e.g., "2023-10-01T12:00").
 * @see https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/datetime-local
 *
 * @remarks
 *
 * So for some reason, the datetime-local input field requires ISO Datetime as value.
 *
 * But the standard`date.toISOString()` returns everything with seconds and milliseconds,
 * which the input field doesn't like (on chrome, on firefox its fine)
 *
 * On chrome, setting .valueAsNumber works, but that causes an error on firefox, so go figure.
 *
 * Additionally, `toISOString` always returns the date without timezone,
 * which we would like to include for better usability
 */
export function dateTimeLocal(input: Date): string {
    const tzOffset = new Date().getTimezoneOffset() * 60_000; //offset in milliseconds
    const localISOTime = new Date(input.getTime() - tzOffset).toISOString().slice(0, -1);

    const [datePart, timePart] = localISOTime.split(":");

    return [datePart, timePart].join(":");
}

/**
 * Convert a Date object to UTC.
 *
 * @remarks
 *
 * Sigh...so our API is UTC/can take TZ info in the ISO format as it should.
 *
 * datetime-local fields (which is almost the only date-time input we use)
 * can return its value as a UTC timestamp...however the generated API client
 * _requires_ a Date object, only to then convert it to an ISO string anyways
 * JS Dates don't include timezone info in the ISO string, so that just sends
 * the local time as UTC...which is wrong.
 *
 * Instead we have to do this, convert the given date to a UTC timestamp,
 * then subtract the timezone offset to create an "invalid" date (correct time&date)
 * but it still "thinks" it's in local TZ.
 */
export function dateToUTC(input: Date): Date {
    const timestamp = input.getTime();
    const offset = -1 * (new Date().getTimezoneOffset() * 60_000);

    return new Date(timestamp - offset);
}
