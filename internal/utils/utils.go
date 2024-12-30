package utils

import "goauthentik.io/internal/config"

var log = config.Get().Logger().Named("authentik.utils")
