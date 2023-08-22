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
};
