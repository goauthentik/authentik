import { html, TemplateResult } from "lit-html";
import { SpinnerSize } from "./elements/Spinner";

export function getCookie(name: string): string {
    let cookieValue = "";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function convertToSlug(text: string): string {
    return text
        .toLowerCase()
        .replace(/ /g, "-")
        .replace(/[^\w-]+/g, "");
}

export function truncate(input?: string, max = 10): string {
    input = input || "";
    const array = input.trim().split(" ");
    const ellipsis = array.length > max ? "..." : "";

    return array.slice(0, max).join(" ") + ellipsis;
}

export function htmlFromString(...strings: string[]): TemplateResult {
    return html(<TemplateStringsArray><unknown>strings);
}

export function loading<T>(v: T, actual: TemplateResult): TemplateResult {
    if (!v) {
        return html`<div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <div class="pf-l-bullseye">
                    <div class="pf-l-bullseye__item">
                        <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                    </div>
                </div>
            </div>
        </div>`;
    }
    return actual;
}

export function time(t: string): Date {
    return new Date(parseInt(t, 10) * 1000);
}
