package handler

import (
	"net/http"

	"github.com/Rippling/interneers-lab-2026/pkg/helloworld/controller"
)

func RegisterHelloHandler(mux *http.ServeMux) {
	helloController := controller.NewHelloController()
	helloHandler := NewHelloHandler(helloController)

	mux.HandleFunc("/hello", helloHandler.Hello)
	mux.HandleFunc("/hello-world", helloHandler.HelloWorld)
}
