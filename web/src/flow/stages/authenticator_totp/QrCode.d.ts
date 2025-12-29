import { type QRCode } from "webcomponent-qr-code";

declare global {
    interface HTMLElementTagNameMap {
        "qr-code": QRCode;
    }
}
