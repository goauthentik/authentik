/* eslint-env jquery */

class SimpleFlowExecutor {
    challenge;
    flowSlug;
    container;

    constructor(container) {
        this.flowSlug = window.location.pathname.split("/")[3];
        this.container = container;
    }

    get apiURL() {
        return `/api/v3/flows/executor/${this.flowSlug}/?query=${encodeURIComponent(window.location.search.substring(1))}`;
    }

    start() {
        $.ajax({
            type: "GET",
            url: this.apiURL,
            success: (data) => {
                this.challenge = data;
                this.renderChallenge();
            },
        });
    }

    submit(data) {
        $("button[type=submit]").addClass("disabled")
            .html(`<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span role="status">Loading...</span>`);
        var object = {};
        data.forEach((value, key) => (object[key] = value));
        $.ajax({
            type: "POST",
            url: this.apiURL,
            data: JSON.stringify(object),
            success: (data) => {
                this.challenge = data;
                this.renderChallenge();
            },
            contentType: "application/json",
            dataType: "json",
        });
    }

    renderChallenge() {
        switch (this.challenge.component) {
            case "ak-stage-identification":
                new IdentificationStage(this).render();
                return;
            case "ak-stage-password":
                new PasswordStage(this).render();
                return;
            case "xak-flow-redirect":
                new RedirectStage(this).render();
                return;
            case "ak-stage-autosubmit":
                new AutosubmitStage(this).render();
                return;
            case "ak-stage-authenticator-validate":
                new AuthenticatorValidateStage(this).render();
                return;
            default:
                this.container.innerText = "Unsupported stage: " + this.challenge.component;
                return;
        }
    }
}

class Stage {
    constructor(executor) {
        this.executor = executor;
    }
    error(fieldName) {
        if (!this.executor.challenge.response_errors) {
            return [];
        }
        return this.executor.challenge.response_errors[fieldName] || [];
    }
    html(html) {
        this.executor.container.innerHTML = html;
    }
    render() {
        throw new Error("Abstract method");
    }
}

class IdentificationStage extends Stage {
    render() {
        this.html(`
            <form id="ident-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                ${
                    this.executor.challenge.application_pre
                        ? `<p>
                              Login to continue to ${this.executor.challenge.application_pre}.
                          </p>`
                        : ""
                }
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control" name="uid_field" placeholder="Email / Username">
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">${this.executor.challenge.primary_action}</button>
            </form>`);
        $("#ident-form input").focus();
        $("#ident-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }
}

class PasswordStage extends Stage {
    render() {
        this.html(`
            <form id="password-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="password" autofocus class="form-control ${this.error("password").length > 0 ? "is-invalid" : ""}" name="password" placeholder="Password">
                    ${this.error("password").map((error) => {
                        return `<div class="invalid-feedback">
                                ${error.string}
                            </div>`;
                    })}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#password-form input").focus();
        $("#password-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }
}

class RedirectStage extends Stage {
    render() {
        window.location.assign(this.executor.challenge.to);
    }
}

class AutosubmitStage extends Stage {
    render() {
        this.html(`
            <form id="autosubmit-form" action="${this.executor.challenge.url}" method="POST">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                ${Object.entries(this.executor.challenge.attrs).map(([key, value]) => {
                    return `<input
                            type="hidden"
                            name="${key}"
                            value="${value}"
                        />`;
                })}
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            </form>`);
        $("#autosubmit-form").submit();
    }
}

class AuthenticatorValidateStage extends Stage {
    render() {
        this.html(`
            <form id="totp-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control ${this.error("code").length > 0 ? "is-invalid" : ""}" name="code" placeholder="Please enter your code" autocomplete="one-time-code">
                    ${this.error("code").map((error) => {
                        return `<div class="invalid-feedback">
                                ${error.string}
                            </div>`;
                    })}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#totp-form input").focus();
        $("#totp-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }
}

const sfe = new SimpleFlowExecutor($("#flow-sfe-container")[0]);
sfe.start();
