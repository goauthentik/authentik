package flow

import "github.com/golang-jwt/jwt/v5"

type SessionCookieClaims struct {
	jwt.Claims

	SessionID     string `json:"sid"`
	Authenticated bool   `json:"authenticated"`
}

func (fe *FlowExecutor) Session() *jwt.Token {
	sc := fe.SessionCookie()
	if sc == nil {
		return nil
	}
	t, _, _ := jwt.NewParser().ParseUnverified(sc.Value, &SessionCookieClaims{})
	return t
}
