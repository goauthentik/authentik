declare namespace AppleID {
    const auth: AppleIDAuth;

    interface AppleIDAuthInit {
        clientId: string;
        scope: string;
        redirectURI: string;
        state: string;
        usePopup: boolean;
    }

    class AppleIDAuth {
        init(options: AppleIDAuthInit): void;
        signIn(): Promise<void>;
    }
}
