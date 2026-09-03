using System.IO;
using System.Text.Json;

namespace Anastaria.Launcher;

public sealed class LauncherSettings
{
    public Uri ApiBaseUrl { get; init; } = new("http://localhost:5000/api/v1/");
    public Uri WebsiteUrl { get; init; } = new("http://localhost:3000/");
    public string GameExecutablePath { get; init; } = string.Empty;
    public Uri? PatchManifestUrl { get; init; }
    public string PatchPublicKeyPem { get; init; } = string.Empty;

    public static LauncherSettings Load()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "launcher-settings.json");
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<LauncherSettings>(json, JsonOptions)
            ?? throw new InvalidDataException("Launcher settings are invalid.");
    }

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };
}
