# ANASTARIA Launcher

The Windows launcher MVP lives in `Anastaria.Launcher/` and uses .NET 10 WPF.
It consumes only the typed ANASTARIA API for authentication, server status,
news, events, and shop data.

## Run

```powershell
dotnet run --project .\Anastaria.Launcher\Anastaria.Launcher.csproj
```

Development URLs and the client executable path are stored in
`launcher-settings.json`. Production packaging must replace these with HTTPS
URLs and a path relative to the installed launcher.

The patcher is intentionally disabled until `patchManifestUrl` is configured.
Its manifest contains a version and a list of files with relative path, HTTPS
download URL, byte size, and SHA-256 hash. Downloads are verified before they
replace installed files, and manifest paths cannot escape the installation
directory.
