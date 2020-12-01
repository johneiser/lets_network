# termshark v1.0.0
FROM golang:latest
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -qy tshark
ENV GO111MODULE=on
RUN go get github.com/gcla/termshark/v2/cmd/termshark
