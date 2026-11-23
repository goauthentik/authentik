declare namespace AppleID {
    const auth: AppleIDAuth;

    class AppleIDAuth {
        init(options: {
            clientId: string;
            scope: string;
            redirectURI: string;
            state: string;
            usePopup: boolean;
        }): void;
        signIn(): Promise<void>;
    }
}
