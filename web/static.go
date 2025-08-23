package web

import (
	_ "embed"
	"net/http"
)

//go:embed robots.txt
var RobotsTxt []byte

//go:embed security.txt
var SecurityTxt []byte

var StaticDir = http.Dir("./web/dist/")

var StaticHandler = http.FileServer(StaticDir)
