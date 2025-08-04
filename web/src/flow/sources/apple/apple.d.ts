declare namespace AppleID {
    const auth: AppleIDAuth;

    class AppleIDAuth {
        public init({
            clientId: string,
            scope: string,
            redirectURI: string,
            state: string,
            usePopup: boolean,
        }): void;
        public async signIn(): Promise<void>;
    }
}
