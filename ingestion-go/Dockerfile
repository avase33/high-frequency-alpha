FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /hfa-ingestion .

FROM gcr.io/distroless/static-debian12
COPY --from=build /hfa-ingestion /hfa-ingestion
ENV HFA_ADDR=:8080
EXPOSE 8080
ENTRYPOINT ["/hfa-ingestion"]
