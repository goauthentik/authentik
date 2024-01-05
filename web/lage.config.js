module.exports = {
    pipeline: {
        "build": [],
        "lint": [],
        "tsc": [],
        "lit-analyse": [],
        "lint:precommit": [],
        "lint:spelling": [],
        "precommit-all": ["tsc", "lit-analyse", "lint:precommit", "lint:spelling", "prettier"],
        "build-locales": ["^build-locales"],
        "extract-locales": ["^extract-locales"],
        "watch": ["authentik#watch"],
        "web-fix": ["^web-lint-fix", "^web-lint", "^web-check-compile", "^web-i18n-extract"],
        "prettier": ["^prettier"],
        
            
    },
};
