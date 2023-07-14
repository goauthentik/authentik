test:
	go test -v

cover:
	rm -rf *.coverprofile
	go test -coverprofile=fresh.coverprofile
	gover
	go tool cover -html=fresh.coverprofile