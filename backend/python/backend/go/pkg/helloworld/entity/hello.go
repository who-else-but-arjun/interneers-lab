package entity

type HelloRequest struct {
	Name string `json:"name"`
}

func NewHelloRequest(name string) *HelloRequest {
	return &HelloRequest{Name: name}
}

type HelloResponse struct {
	Message string `json:"message"`
}
