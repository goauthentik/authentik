package backend

import (
	"bytes"
	"os/exec"
)

func OpensslVersion() string {
	cmd := exec.Command("openssl", "version")
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		return ""
	}
	return out.String()
}
