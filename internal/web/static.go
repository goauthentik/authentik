package web

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/go-http-utils/etag"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/mux"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/utils/web"
	staticWeb "goauthentik.io/web"
)

// Theme variable placeholder that can be used in file paths
// This allows for theme-specific files like logo-%(theme)s.png
const themeVariable = "%(theme)s"

// Valid themes that can be substituted for %(theme)s
var validThemes = []string{"light", "dark"}

type StorageClaims struct {
	jwt.RegisteredClaims
	Path string `json:"path,omitempty"`
}

// pathMatchesWithTheme checks if the requested path matches the JWT path,
// accounting for theme variable substitution.
// If the JWT path contains %(theme)s, it will match the requested path
// if substituting %(theme)s with any valid theme produces the requested path.
func pathMatchesWithTheme(jwtPath, requestedPath string) bool {
	// Direct match (no theme variable)
	if jwtPath == requestedPath {
		return true
	}

	// Check if JWT path contains theme variable
	if !strings.Contains(jwtPath, themeVariable) {
		return false
	}

	// Try substituting each valid theme and check for a match
	for _, theme := range validThemes {
		substituted := strings.ReplaceAll(jwtPath, themeVariable, theme)
		if substituted == requestedPath {
			return true
		}
	}

	return false
}

func storageTokenIsValid(usage string, r *http.Request) bool {
	tokenString := r.URL.Query().Get("token")
	if tokenString == "" {
		return false
	}
	claims := &StorageClaims{}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method")
		}
		key := []byte(fmt.Sprintf("%s:%s", config.Get().SecretKey, usage))
		hash := sha256.Sum256(key)
		hexDigest := hex.EncodeToString(hash[:])
		return []byte(hexDigest), nil
	})
	if err != nil || !token.Valid {
		return false
	}

	now := time.Now()

	if claims.ExpiresAt != nil && claims.ExpiresAt.Before(now) {
		return false
	}
	if claims.NotBefore != nil && claims.NotBefore.After(now) {
		return false
	}

	requestedPath := fmt.Sprintf("%s/%s", usage, r.URL.Path)
	if !pathMatchesWithTheme(claims.Path, requestedPath) {
		return false
	}

	return true
}

func (ws *WebServer) configureStatic() {
	// Setup routers
	staticRouter := ws.loggingRouter.NewRoute().Subrouter()
	staticRouter.Use(ws.staticHeaderMiddleware)
	staticRouter.Use(web.DisableIndex)

	distFs := http.FileServer(http.Dir("./web/dist"))

	pathStripper := func(handler http.Handler, paths ...string) http.Handler {
		h := handler
		for _, path := range paths {
			h = http.StripPrefix(path, h)
		}
		return h
	}

	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/dist/").Handler(pathStripper(
		distFs,
		"static/dist/",
		config.Get().Web.Path,
	))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/authentik/").Handler(pathStripper(
		http.FileServer(http.Dir("./web/authentik")),
		"static/authentik/",
		config.Get().Web.Path,
	))

	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/flow/"+vars["flow_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/admin/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/admin", config.Get().Web.Path), distFs))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/user/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/user", config.Get().Web.Path), distFs))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/rac/{app_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/rac/"+vars["app_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})

	// Files, if backend is file
	defaultBackend := config.Get().Storage.Backend
	if defaultBackend == "" {
		defaultBackend = "file"
	}
	mediaBackend := config.Get().Storage.Media.Backend
	if mediaBackend == "" {
		mediaBackend = defaultBackend
	}
	reportsBackend := config.Get().Storage.Reports.Backend
	if reportsBackend == "" {
		reportsBackend = defaultBackend
	}

	defaultStoragePath := config.Get().Storage.File.Path
	if defaultStoragePath == "" {
		defaultStoragePath = "./data"
	}

	if mediaBackend == "file" {
		mediaPath := config.Get().Storage.Media.File.Path
		if mediaPath == "" {
			mediaPath = defaultStoragePath
		}
		mediaPath = mediaPath + "/media"
		fsMedia := http.FileServer(http.Dir(mediaPath))
		staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/media/").Handler(pathStripper(
			http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if !storageTokenIsValid("media", r) {
					http.Error(w, "404 page not found", http.StatusNotFound)
					return
				}

				w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
				fsMedia.ServeHTTP(w, r)
			}),
			"files/media/",
			config.Get().Web.Path,
		))
	}

	if reportsBackend == "file" {
		reportsPath := config.Get().Storage.Reports.File.Path
		if reportsPath == "" {
			reportsPath = defaultStoragePath
		}
		reportsPath = reportsPath + "/reports"
		fsReports := http.FileServer(http.Dir(reportsPath))
		staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/reports/").Handler(pathStripper(
			http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if !storageTokenIsValid("reports", r) {
					http.Error(w, "404 page not found", http.StatusNotFound)
					return
				}
				fsReports.ServeHTTP(w, r)
			}),
			"files/reports/",
			config.Get().Web.Path,
		))
	}

	staticRouter.PathPrefix(config.Get().Web.Path).Path("/robots.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		_, err := rw.Write(staticWeb.RobotsTxt)
		if err != nil {
			ws.log.WithError(err).Warning("failed to write response")
		}
	})
	staticRouter.PathPrefix(config.Get().Web.Path).Path("/.well-known/security.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		_, err := rw.Write(staticWeb.SecurityTxt)
		if err != nil {
			ws.log.WithError(err).Warning("failed to write response")
		}
	})
}

func (ws *WebServer) staticHeaderMiddleware(h http.Handler) http.Handler {
	etagHandler := etag.Handler(h, false)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "public, no-transform")
		w.Header().Set("X-authentik-version", constants.VERSION())
		w.Header().Set("Vary", "X-authentik-version, Etag")
		etagHandler.ServeHTTP(w, r)
	})
}
