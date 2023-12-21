package web

import (
	_ "embed"
	"net/http"
)

//go:embed robots.txt
var RobotsTxt []byte

//go:embed security.txt
var SecurityTxt []byte

var StaticHandler = http.FileServer(http.Dir("./web/dist/"))
