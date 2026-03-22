package handler

import (
	"context"
	"errors"
	"net/http"

	"github.com/rs/zerolog/log"

	"github.com/Rippling/interneers-lab-2026/pkg/helloworld/controller"
)

type HelloHandler struct {
	controller controller.HelloController
}

func NewHelloHandler(c controller.HelloController) *HelloHandler {
	return &HelloHandler{controller: c}
}

func (h *HelloHandler) Hello(w http.ResponseWriter, r *http.Request) {
	log.Info().Str("method", r.Method).Str("path", r.URL.Path).Msg("Hello request received")

	if r.Method != http.MethodGet {
		HandleError(r.Context(), w, r, errors.New("method not allowed"), http.StatusMethodNotAllowed)
		return
	}

	req, err := MapHTTPRequestToHelloRequest(r)
	if err != nil {
		HandleError(r.Context(), w, r, err, http.StatusBadRequest)
		return
	}

	resp, err := h.controller.Hello(r.Context(), req)
	if err != nil {
		HandleError(r.Context(), w, r, err, http.StatusInternalServerError)
		return
	}

	MapHelloResponseToHTTPResponse(resp, w)
}

func (h *HelloHandler) HelloWorld(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	log.Ctx(ctx).Info().Str("method", r.Method).Str("path", r.URL.Path).Msg("HelloWorld request received")

	if !IsGetMethod(ctx, w, r) {
		return
	}

	resp, err := h.controller.HelloWorld(ctx)
	if err != nil {
		HandleError(ctx, w, r, err, http.StatusInternalServerError)
		return
	}

	MapHelloResponseToHTTPResponse(resp, w)
}

func IsGetMethod(ctx context.Context, w http.ResponseWriter, r *http.Request) bool {
	if r.Method == http.MethodGet {
		return true
	}

	return false
}

func HandleError(ctx context.Context, w http.ResponseWriter, r *http.Request, err error, statusCode int) {
	log.Ctx(ctx).Error().Err(err).Msg("Failed to process request")
	http.Error(w, err.Error(), statusCode)
}
