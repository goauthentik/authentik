test:
	go test -v

cover:
	rm -rf *.coverprofile
	go test -coverprofile=etag.coverprofile
	gover
	go tool cover -html=etag.coverprofile