package controller

import (
	"context"

	"github.com/Rippling/interneers-lab-2026/pkg/helloworld/entity"
)

type HelloController interface {
	Hello(ctx context.Context, request *entity.HelloRequest) (*entity.HelloResponse, error)
	HelloWorld(ctx context.Context) (*entity.HelloResponse, error)
}

type helloController struct{}

func NewHelloController() HelloController {
	return &helloController{}
}

func (c *helloController) Hello(ctx context.Context, request *entity.HelloRequest) (*entity.HelloResponse, error) {
	return &entity.HelloResponse{Message: "Hello, " + request.Name + "!"}, nil
}

func (c *helloController) HelloWorld(ctx context.Context) (*entity.HelloResponse, error) {
	return &entity.HelloResponse{Message: "Hello, World!"}, nil
}
