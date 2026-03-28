# Dev Machine Setup - Chess Vision Project

**Last Updated:** 2026-03-28  
**Connection Method:** SSH tunnel + Docker remote API

## Connection Details

**Remote Machine:**  
- Host: `100.120.200.17`  
- User: `jan`  
- SSH Key: Installed (passwordless auth available)

**Docker Access:**
- Local Tunnel Port: `2375`
- Docker Host: `tcp://127.0.0.1:2375`
- API Endpoint: `http://127.0.0.1:2375`

## Quick Commands

### Establish SSH Tunnel (One-time per session)
```bash
ssh -N -L 127.0.0.1:2375:127.0.0.1:2375 jan@100.120.200.17 -f
```

### Configure Docker Client
```bash
export DOCKER_HOST=tcp://127.0.0.1:2375
```

### Verify Connection
```bash
curl http://127.0.0.1:2375/_ping
docker version
docker ps -a
```

## Container Operations

### Build Container
```bash
DOCKER_HOST=tcp://127.0.0.1:2375 docker build -t chess-vision-dev .
```

### Run Container
```bash
DOCKER_HOST=tcp://127.0.0.1:2375 docker run -it --rm \
  -v $(pwd):/app \
  -p 8080:8080 \
  chess-vision-dev
```

### List Containers
```bash
DOCKER_HOST=tcp://127.0.0.1:2375 docker ps -a
```

## Project Workflow

**IMPORTANT:** When developing for ChessVision:
1. Always use this Docker setup on the dev machine
2. Do NOT build/run containers locally
3. All containers spawn on the remote dev machine (100.120.200.17)
4. Keep the SSH tunnel active during development

## Flutter Development

Once inside the dev container:
```bash
flutter pub get
flutter build apk
flutter test
```

## History

- 2026-03-28: SSH tunnel established, Docker verified working
- Container creation tested successfully
- All future agent work should use this configuration
