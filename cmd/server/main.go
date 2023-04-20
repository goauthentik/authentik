package main

import "os"

func main() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}
