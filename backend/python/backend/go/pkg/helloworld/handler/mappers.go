package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/Rippling/interneers-lab-2026/pkg/helloworld/entity"
)

func MapHTTPRequestToHelloRequest(r *http.Request) (*entity.HelloRequest, error) {
	name := r.URL.Query().Get(entity.HelloNameQueryParam)
	if name == "" {
		return nil, errors.New("name is required")
	}
	return entity.NewHelloRequest(name), nil
}

func MapHelloResponseToHTTPResponse(resp *entity.HelloResponse, w http.ResponseWriter) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
