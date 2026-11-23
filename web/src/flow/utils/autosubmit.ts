import { AutosubmitChallenge } from "@goauthentik/api";

export function submitAutosubmitChallenge(challenge: AutosubmitChallenge): void {
    const form = document.createElement("form");
    form.action = challenge.url;
    form.method = "post";
    form.hidden = true;

    for (const [name, value] of Object.entries(challenge.attrs)) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        form.append(input);
    }

    document.body.append(form);
    HTMLFormElement.prototype.submit.call(form);
}
