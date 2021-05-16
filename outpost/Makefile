all: clean generate

generate:
	go get -u github.com/go-swagger/go-swagger/cmd/swagger
	swagger generate client -f ../schema.yml -A authentik -t pkg/

run:
	go run -v .

clean:
	go mod tidy
	go clean .

