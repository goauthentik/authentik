package web

import "goauthentik.io/internal/config"

var log = config.Get().Logger().Named("authentik.utils.web")
