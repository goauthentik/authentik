/**
 * @file QR code web component type definitions.
 */

declare module "webcomponent-qr-code" {
    /**
     * QR Code Web Component
     *
     * @element qr-code
     *
     * @attr {"svg" | "png" | "html"} format - The type of QR code to generate.
     * @attr {string} data - The data to encode in the QR code.
     *
     * @see {@link https://www.webcomponents.org/element/webcomponent-qr-code}
     */
    class QRCode extends HTMLElement {}

    export default QRCode;
}
