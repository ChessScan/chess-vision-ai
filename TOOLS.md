# TOOLS.md - Local Notes

**🔐 Credentials:** See [CREDENTIALS.md](./CREDENTIALS.md) for all API keys, tokens, and secrets.

---

### GitHub Organization

**Org:** `ChessScan`  
**Repos:**
- `chess-vision-ai` - Model training & CV dev (this repo)
- `chess-vision-app` - Mobile app
- `chess-vision-docs` - Documentation & planning

### Dev Containers

| Repo | Container | Purpose | Image | Status |
|------|-----------|---------|-------|--------|
| chess-vision-ai | cv-dev | Python/OpenCV/TF/Jupyter | `chess-vision:dev` | ✅ |
| chess-vision-ai | blender-synth | Blender 4.0 synthetic data | `chess-vision/blender-synth:latest` | ✅ **ON DEV MACHINE** |
| chess-vision-ai | training | PyTorch/CUDA training | `chess-vision:training` | ✅ |
| chess-vision-app | app-dev | React Native/Expo | `chess-vision-app:dev` | ✅ **RUNNING** |
| chess-vision-docs | docs-dev | MkDocs Material | `chess-vision-docs:dev` | ⏳ staged |

### Dev Machine
**Host:** `jan@100.120.200.17`  
**Docker:** `tcp://127.0.0.1:2375` (Podman 4.9.3)  
**Specs:** Ryzen 9 5900XT @ 32 threads, 62GB RAM  
**Data:** `/home/jan/Desktop/chess/` (116,771 renders from alpha prototype)

---

### Discord Channels

| Channel | ID | Purpose |
|---------|-----|---------|
| trace-status | `1487204636627566622` | Hourly activity updates |
| chess-app | `1487202132493996064` | App dev - UI/UX, features |
| ai-training | `1487202132821278760` | Model training |
| project-general | `1487202132892586165` | Project planning |
| vision | `1487202133098106960` | Computer vision work |
| pull-requests | `1487203171955638404` | PR notifications |
