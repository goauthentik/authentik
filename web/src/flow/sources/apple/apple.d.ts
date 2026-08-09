declare namespace AppleID {
    const auth: AppleIDAuth;

    class AppleIDAuth {
        init({
            clientId: string,
            scope: string,
            redirectURI: string,
            state: string,
            usePopup: boolean,
        }): void;
        async signIn(): Promise<void>;
    }
}
