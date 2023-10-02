function generateNavbarDropdown(label, categories, extra) {
    return `<a aria-haspopup="true" aria-expanded="false" role="button" class="navbar__link">${label}</a>
    <div class="dropdown__menu">
        ${categories
            .map(({ label, items }) => {
                return `<div class="category">
                <p>${label}</p>
                <ul>
                ${items
                    .map(({ to, label }) => {
                        return `<li><a class="dropdown__link" href="${to}">${label}</a></li>`;
                    })
                    .join("")}
            </ul>
            </div>`;
            })
            .join("")}
        ${extra ?? ""}
    </div>`;
}

function generateVersionDropdown(sidebar) {
    const releases = sidebar.docs
        .filter((doc) => doc.link?.slug === "releases")[0]
        .items.filter((release) => typeof release === "string");
    const latest = releases[0].replace(/releases\/\d+\/v/, "");
    return `<div class="navbar__item dropdown dropdown--hoverable dropdown--right">
        <div aria-haspopup="true" aria-expanded="false" role="button" class="navbar__link menu__link">
            Version: ${latest}
        </div>
        <ul class="dropdown__menu">
            ${releases
                .map((release) => {
                    const version = release.replace(/releases\/\d+\/v/, "");
                    const subdomain = `version-${version.replace(".", "-")}`;
                    const label = `Version: ${version}`;
                    return `<li>
                            <a
                                href="https://${subdomain}.goauthentik.io/docs"
                                target="_blank" rel="noopener noreferrer"
                                class="dropdown__link">${label}</a>
                        </li>`;
                })
                .join("")}
        </ul>
    </div>
    <hr>`;
}

module.exports = {
    generateVersionDropdown,
    generateNavbarDropdown,
};
