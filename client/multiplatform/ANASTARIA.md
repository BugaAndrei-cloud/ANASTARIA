# ANASTARIA multiplatform client

This directory contains the ANASTARIA adaptation of the MonoGame MU Online
client. It is kept separate from `client/pc/MuMain-Source` so the established
desktop client remains available during the migration.

Upstream source: `https://github.com/bernatvadell/muonline.git`, imported from
commit `7baa3454b890c1b33189fd2bc89c7f6d7af3058d`.

## OpenMU protocol profile

The checked-in defaults match the open-source client definition created by the
ANASTARIA OpenMU Season 6 initializer:

- protocol: Season 6 Episode 3 (extended open-source protocol)
- client version: `2.04d`
- client serial: `k1Pk2jcET48mxL3b`
- connect-server port: `44406`
- development host: `192.168.55.220`

OpenMU assigns `44405` to the original `1.04d` client and `44406` to the
extended `2.04d` open-source client. Do not point this client at `44405` unless
the server endpoint definitions have been changed accordingly.

The development host is a LAN address. Replace `ConnectServerHost` in
`Client.Main/appsettings.json` with the public DNS name or public IP before a
release build. Mobile devices must be able to reach that address directly.

## Data files

Proprietary MU data is deliberately not committed. Supply the required Season
20 data plus the Season 6 patch as described in the upstream `README.md`.
`Constants.DataPathUrl` currently targets the ANASTARIA development host and
must point to a reachable HTTPS asset endpoint before public mobile releases.

## Verification commands

Run these commands from this directory:

```powershell
dotnet tool restore
dotnet build .\MuWinDX\MuWinDX.csproj -c Debug -p:MonoGameFramework=MonoGame.Framework.WindowsDX
dotnet build .\MuWinGL\MuWinGL.csproj -c Debug -p:MonoGameFramework=MonoGame.Framework.DesktopGL
```

Android requires the .NET Android workload and an Android SDK/JDK:

```powershell
dotnet workload restore .\MuAndroid\MuAndroid.csproj
dotnet build .\MuAndroid\MuAndroid.csproj -c Debug `
  -p:AndroidSdkDirectory=.\.android\sdk `
  -p:JavaSdkDirectory=<path-to-jdk-17>
```

On the current Windows development machine, the local Android SDK is kept in
`.android/sdk` and JDK 17 is installed per-user. The generated debug APK is
written under `MuAndroid/bin/Debug/net10.0-android/`.

iOS compilation and signing require macOS, Xcode, the .NET iOS workload, and
an Apple development identity:

```bash
dotnet workload restore ./MuIos/MuIos.csproj
dotnet build ./MuIos/MuIos.csproj -c Debug
```
