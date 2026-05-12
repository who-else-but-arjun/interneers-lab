package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	helloworldhandler "github.com/Rippling/interneers-lab-2026/pkg/helloworld/handler"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func RegisterRoutes(mux *http.ServeMux) {
	helloworldhandler.RegisterHelloHandler(mux)
}

func GetPort() string {
	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8000"
	}
	return port
}

func setupZerolog() {
	zerolog.TimeFieldFormat = time.RFC3339
	log.Logger = zerolog.New(os.Stdout).With().Timestamp().Logger()
}

func main() {
	setupZerolog()
	port := GetPort()

	mux := http.NewServeMux()
	RegisterRoutes(mux)

	addr := fmt.Sprintf(":%s", port)
	log.Info().Str("port", port).Msg("Server starting")
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal().Err(err).Msg("Server failed to start")
	}
}
