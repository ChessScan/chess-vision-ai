# Mobile App Development Container

## Quick Start

```bash
cd docker
docker-compose up -d app-dev
docker exec -it chess-vision-app-dev bash
```

## Usage

```bash
# Inside container - start Expo development server
npx expo start

# Or React Native CLI
npx react-native start
```

## Notes

- **iOS builds**: Require macOS host with Xcode
- **Android builds**: Can build APK in container
- **Expo**: Runs development client accessible on LAN
- **Hot reload**: Works via volume mounts

## Ports

| Port | Service |
|------|---------|
| 8081 | Metro bundler |
| 19000 | Expo Go |
| 19006 | Expo Web |
| 19001-19002 | Expo DevTools |
