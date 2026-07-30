//go:build outpost_static_embed

package web

import (
	"embed"
	"net/http"
)

//go:embed dist/*
var StaticDist embed.FS

//go:embed authentik
var StaticAuthentik embed.FS

func init() {
	StaticHandler = http.FileServer(http.FS(StaticDist))
}
