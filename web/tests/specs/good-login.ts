import { login } from "../utils/login.js";

describe("Log into authentik", () => {
    it("should login with valid credentials and reach the UserLibrary", login);
});
