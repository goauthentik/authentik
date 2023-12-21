import { User } from "@goauthentik/api";

export function UserOption(user: User): string {
    let finalString = user.username;
    if (user.name || user.email) {
        finalString += " (";
        if (user.name) {
            finalString += user.name;
            if (user.email) {
                finalString += ", ";
            }
        }
        if (user.email) {
            finalString += user.email;
        }
        finalString += ")";
    }
    return finalString;
}
