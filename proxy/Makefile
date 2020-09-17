all: clean generate build

generate:
	go get -u github.com/go-swagger/go-swagger/cmd/swagger
	swagger generate client -f ../swagger.yaml -A passbook -t pkg/

run:
	go run -v .

clean:
	go mod tidy
	go clean .

build:
	go build -v .
