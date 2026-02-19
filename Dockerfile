# NeuroFlow服务的Dockerfile
# 基于Alpine Linux以获得较小的镜像尺寸

# 构建阶段
FROM rust:1.75-alpine AS builder

# 安装构建依赖
RUN apk add --no-cache musl-dev protobuf-dev protoc

WORKDIR /usr/src/kernel

# 复制Cargo文件
COPY kernel/Cargo.toml kernel/Cargo.lock ./

# 创建一个空的src目录以便能够构建依赖
RUN mkdir src && echo "fn main() { }" > src/main.rs

# 构建依赖
RUN cargo build --release

# 清理以重新构建
RUN rm -rf src

# 复制源代码
COPY kernel/src ./src
COPY proto ./proto

# 构建应用
RUN cargo build --release

# 运行阶段
FROM alpine:latest

# 安装必要的运行时依赖
RUN apk add --no-cache ca-certificates libgcc

# 创建非root用户
RUN addgroup -g 1000 -S appgroup && \
    adduser -u 1000 -S appuser -G appgroup

WORKDIR /usr/src/app

# 从构建阶段复制二进制文件
COPY --from=builder /usr/src/kernel/target/release/kernel .

# 更改所有权
RUN chown -R appuser:appgroup /usr/src/app
USER appuser

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["./kernel"]