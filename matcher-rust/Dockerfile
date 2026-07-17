FROM rust:1.79-slim AS build
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release --bin hfa-matcher

FROM debian:bookworm-slim
COPY --from=build /app/target/release/hfa-matcher /usr/local/bin/hfa-matcher
ENV MATCHER_ADDR=0.0.0.0:8091
EXPOSE 8091
CMD ["hfa-matcher"]
