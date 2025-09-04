#!/bin/bash

# Tax Sale Compass - Optimized Build Script
# Leverages Docker BuildKit for faster builds with caching

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="taxsale-compass"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
BUILD_CACHE_DIR="${BUILD_CACHE_DIR:-/tmp/buildx-cache}"
PARALLEL_BUILDS="${PARALLEL_BUILDS:-true}"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Enable BuildKit
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    # Check if buildx is available
    if docker buildx version &> /dev/null; then
        success "Docker BuildKit available"
    else
        warning "Docker BuildKit not available, using standard build"
    fi
}

# Setup build cache
setup_cache() {
    if [ "$PARALLEL_BUILDS" = "true" ] && docker buildx version &> /dev/null; then
        log "Setting up build cache..."
        
        # Create cache directory
        mkdir -p "$BUILD_CACHE_DIR"
        
        # Create buildx builder if it doesn't exist
        if ! docker buildx inspect multiplatform-builder &> /dev/null; then
            log "Creating buildx builder..."
            docker buildx create --name multiplatform-builder --use --bootstrap
        else
            docker buildx use multiplatform-builder
        fi
        
        success "Build cache setup complete"
    fi
}

# Build with optimizations
build_optimized() {
    log "Starting optimized build process..."
    
    cd "$(dirname "$0")/.."
    
    if [ "$PARALLEL_BUILDS" = "true" ] && docker buildx version &> /dev/null; then
        log "Building with BuildKit and cache optimization..."
        
        docker buildx build \
            --file docker/Dockerfile.production \
            --tag "${PROJECT_NAME}:latest" \
            --tag "${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S)" \
            --cache-from type=local,src="$BUILD_CACHE_DIR" \
            --cache-to type=local,dest="$BUILD_CACHE_DIR",mode=max \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --build-arg REACT_APP_BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}" \
            --build-arg REACT_APP_GOOGLE_MAPS_API_KEY="${REACT_APP_GOOGLE_MAPS_API_KEY:-}" \
            --progress=plain \
            --load \
            .
    else
        log "Building with standard Docker build..."
        
        docker build \
            --file docker/Dockerfile.production \
            --tag "${PROJECT_NAME}:latest" \
            --build-arg REACT_APP_BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}" \
            --build-arg REACT_APP_GOOGLE_MAPS_API_KEY="${REACT_APP_GOOGLE_MAPS_API_KEY:-}" \
            .
    fi
    
    success "Build completed successfully"
}

# Tag and push to registry (if configured)
push_to_registry() {
    if [ -n "$DOCKER_REGISTRY" ]; then
        log "Pushing to registry: $DOCKER_REGISTRY"
        
        # Tag for registry
        docker tag "${PROJECT_NAME}:latest" "${DOCKER_REGISTRY}/${PROJECT_NAME}:latest"
        docker tag "${PROJECT_NAME}:latest" "${DOCKER_REGISTRY}/${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S)"
        
        # Push to registry
        docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}:latest"
        docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S)"
        
        success "Pushed to registry successfully"
    else
        log "No registry configured, skipping push"
    fi
}

# Build performance analysis
analyze_build() {
    log "Analyzing build performance..."
    
    # Get image size
    IMAGE_SIZE=$(docker image inspect "${PROJECT_NAME}:latest" --format='{{.Size}}' | numfmt --to=iec)
    
    # Get layer count
    LAYER_COUNT=$(docker history "${PROJECT_NAME}:latest" --quiet | wc -l)
    
    echo ""
    echo "🏗️ Build Analysis:"
    echo "   📦 Final image size: $IMAGE_SIZE"
    echo "   📚 Number of layers: $LAYER_COUNT"
    echo ""
    
    # Show largest layers
    log "Largest image layers:"
    docker history "${PROJECT_NAME}:latest" --format "table {{.Size}}\t{{.CreatedBy}}" --no-trunc | head -10
}

# Cleanup old images
cleanup() {
    log "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old tagged images (keep last 5)
    OLD_IMAGES=$(docker images "${PROJECT_NAME}" --format "{{.Repository}}:{{.Tag}}" | grep -E '[0-9]{8}-[0-9]{6}$' | tail -n +6)
    if [ -n "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs docker rmi
        success "Cleaned up old images"
    else
        log "No old images to clean up"
    fi
}

# Health check
health_check() {
    log "Running post-build health check..."
    
    # Start container temporarily for health check
    CONTAINER_ID=$(docker run -d -p 8080:80 "${PROJECT_NAME}:latest")
    
    # Wait for container to start
    sleep 10
    
    # Check health endpoint
    if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
        success "Health check passed"
    else
        warning "Health check failed - container may need more time to start"
    fi
    
    # Cleanup test container
    docker stop "$CONTAINER_ID" > /dev/null
    docker rm "$CONTAINER_ID" > /dev/null
}

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-cache       Disable build cache"
    echo "  --no-parallel    Disable parallel builds"
    echo "  --registry URL   Push to specified registry"
    echo "  --analyze        Run build performance analysis"
    echo "  --health-check   Run post-build health check"
    echo "  --cleanup        Clean up old images"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REACT_APP_BACKEND_URL         Backend URL for frontend"
    echo "  REACT_APP_GOOGLE_MAPS_API_KEY Google Maps API key"
    echo "  DOCKER_REGISTRY               Docker registry URL"
    echo "  BUILD_CACHE_DIR               Build cache directory"
    echo "  PARALLEL_BUILDS               Enable/disable parallel builds"
}

# Main execution
main() {
    local run_analysis=false
    local run_health_check=false
    local run_cleanup=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cache)
                BUILD_CACHE_DIR=""
                shift
                ;;
            --no-parallel)
                PARALLEL_BUILDS=false
                shift
                ;;
            --registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            --analyze)
                run_analysis=true
                shift
                ;;
            --health-check)
                run_health_check=true
                shift
                ;;
            --cleanup)
                run_cleanup=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Execute build pipeline
    log "🚀 Starting Tax Sale Compass optimized build..."
    
    check_prerequisites
    setup_cache
    build_optimized
    
    if [ "$run_analysis" = true ]; then
        analyze_build
    fi
    
    push_to_registry
    
    if [ "$run_health_check" = true ]; then
        health_check
    fi
    
    if [ "$run_cleanup" = true ]; then
        cleanup
    fi
    
    success "🎉 Build pipeline completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Test the image: docker run -p 8080:80 ${PROJECT_NAME}:latest"
    echo "  2. Deploy with: docker-compose -f docker/docker-compose.production.yml up -d"
    echo ""
}

# Run main function with all arguments
main "$@"