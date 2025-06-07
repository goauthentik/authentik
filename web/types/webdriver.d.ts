declare namespace WebdriverIO {
    interface Element {
        /**
         * Focus on the element.
         * @monkeypatch
         */
        focus(): Promise<void>;
        /**
         * Blur the element.
         * @monkeypatch
         */
        blur(): Promise<void>;
    }
}
