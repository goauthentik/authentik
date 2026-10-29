package connection

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/gorilla/websocket"
	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"goauthentik.io/internal/outpost/ak"
	api "goauthentik.io/packages/client-go"
)

func writeJSON(t *testing.T, w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	assert.NoError(t, json.NewEncoder(w).Encode(v))
}

// An outpost whose AUTHENTIK_HOST has a path, as it does when authentik runs under
// AUTHENTIK_WEB__PATH, connects to the session websocket below that path
func TestInitSocket_WebPath(t *testing.T) {
	outpost := api.NewOutpost(
		"8d68ac38-bbcf-4beb-a6c9-ad04b2fb1c4a", "rac", api.OUTPOSTTYPEENUM_RAC,
		[]int32{}, []api.Provider{}, api.NullableServiceConnection{}, 60, "rac", map[string]any{},
	)
	outposts := api.NewPaginatedOutpostList(
		*api.NewPagination(0, 0, 1, 1, 1, 1, 1), []api.Outpost{*outpost}, map[string]any{},
	)
	sockets := make(chan string, 2)
	upgrader := websocket.Upgrader{}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /authentik/api/v3/outposts/instances/", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(t, w, outposts)
	})
	mux.HandleFunc("GET /authentik/api/v3/root/config/", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(t, w, ak.MockConfig())
	})
	mux.HandleFunc("/authentik/ws/", func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "Bearer a-token", r.Header.Get("Authorization"))
		sockets <- r.URL.Path
		ws, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		go func() {
			for {
				if _, _, err := ws.ReadMessage(); err != nil {
					return
				}
			}
		}()
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	akURL, err := url.Parse(srv.URL + "/authentik")
	require.NoError(t, err)
	ac := ak.NewAPIController(*akURL, "a-token")
	require.NotNil(t, ac)
	defer ac.Shutdown()
	assert.Equal(t, "/authentik/ws/outpost/8d68ac38-bbcf-4beb-a6c9-ad04b2fb1c4a/", <-sockets)

	c := &Connection{ac: ac, log: log.WithField("logger", "test")}
	require.NoError(t, c.initSocket("a-channel"))
	defer func() { _ = c.ws.Close() }()
	assert.Equal(t, "/authentik/ws/outpost_rac/a-channel/", <-sockets)
}
