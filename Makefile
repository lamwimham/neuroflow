# NeuroFlow Makefile

.PHONY: help build test clean proto-gen docker-build docker-run docker-stop docker-clean deploy-local deploy-dev logs monitor

help:
	@echo "NeuroFlow Build Commands:"
	@echo "  build              - 构建整个项目"
	@echo "  test               - 运行所有测试"
	@echo "  proto-gen          - 生成Protobuf代码"
	@echo "  clean              - 清理构建产物"
	@echo "  docker-build       - 构建Docker镜像"
	@echo "  docker-run         - 使用Docker Compose运行服务"
	@echo "  docker-stop        - 停止Docker服务"
	@echo "  docker-clean       - 删除Docker容器和镜像"
	@echo "  deploy-local       - 部署到本地环境"
	@echo "  deploy-dev         - 部署到开发环境"
	@echo "  logs               - 查看服务日志"
	@echo "  monitor            - 监控服务状态"

build: proto-gen
	cd kernel && cargo build
	cd sdk && pip install -e .

test:
	cd kernel && cargo test
	cd sdk && pytest

proto-gen:
	# 生成Rust protobuf代码
	protoc --proto_path=proto --rust_out=kernel/src/proto proto/*.proto
	# 生成Python protobuf代码
	python -m grpc_tools.protoc -Iproto --python_out=sdk/neuroflow/proto proto/*.proto

clean:
	cd kernel && cargo clean
	rm -rf sdk/neuroflow/proto/*.py
	rm -rf sdk/neuroflow/proto/*.pyc

# 构建Docker镜像
docker-build:
	@echo "Building Docker images..."
	docker-compose -f docker-compose.yml build

# 运行Docker服务
docker-run:
	@echo "Starting NeuroFlow services with Docker Compose..."
	docker-compose -f docker-compose.yml up -d

# 停止Docker服务
docker-stop:
	@echo "Stopping NeuroFlow services..."
	docker-compose -f docker-compose.yml down

# 清理Docker资源
docker-clean:
	@echo "Removing Docker containers and images..."
	docker-compose -f docker-compose.yml down -v --rmi all

# 部署到本地环境
deploy-local: docker-build docker-run
	@echo "NeuroFlow deployed to local environment!"
	@echo "Access the services:"
	@echo "  Kernel API: http://localhost:8080"
	@echo "  Python SDK: http://localhost:8000"
	@echo "  Jaeger UI: http://localhost:16686"
	@echo "  Prometheus: http://localhost:9090"

# 部署到开发环境
deploy-dev:
	@echo "Deploying to development environment..."
	@echo "Environment: DEVELOPMENT"
	DEPLOY_ENV=development docker-compose -f docker-compose.yml up -d

# 查看服务日志
logs:
	@echo "Viewing NeuroFlow service logs..."
	docker-compose -f docker-compose.yml logs -f

# 监控服务
monitor:
	@echo "Monitoring NeuroFlow services..."
	docker-compose -f docker-compose.yml ps