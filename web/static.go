package web

import (
	_ "embed"
	"net/http"
)

//go:embed robots.txt
var RobotsTxt []byte

//go:embed security.txt
var SecurityTxt []byte

var staticDir = "./web/dist/"

var StaticDir = http.Dir(staticDir)

var StaticHandler = http.FileServer(StaticDir)
