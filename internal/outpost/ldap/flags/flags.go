package flags

import (
	"crypto/sha256"
	"encoding/hex"
	"net/http"

	"github.com/golang-jwt/jwt/v5"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/flow"
)

const InvalidUserPK = -1

type UserFlags struct {
	UserInfo   *api.User
	UserPk     int32
	CanSearch  bool
	Session    *http.Cookie
	SessionJWT *jwt.Token
}

func (uf UserFlags) SessionID() string {
	if uf.SessionJWT == nil {
		return ""
	}
	h := sha256.New()
	h.Write([]byte(uf.SessionJWT.Claims.(*flow.SessionCookieClaims).SessionID))
	return hex.EncodeToString(h.Sum(nil))
}
