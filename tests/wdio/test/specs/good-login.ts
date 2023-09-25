import { login } from "../utils/login.js";

describe("Log into Authentik", () => {
    it("should login with valid credentials and reach the UserLibrary", login);
});
