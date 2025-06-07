package flags

import (
	"net/http"

	"goauthentik.io/api/v3"
)

const InvalidUserPK = -1

type UserFlags struct {
	UserInfo  *api.User
	UserPk    int32
	CanSearch bool
	Session   *http.Cookie
}
