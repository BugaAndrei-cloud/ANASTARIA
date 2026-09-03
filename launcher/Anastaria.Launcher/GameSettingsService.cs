using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Anastaria.Launcher;

public sealed record GameSettings(
    int Width, int Height, bool Fullscreen, string QualityPreset, bool VSync,
    int FrameRateLimit, double? RenderScale, bool? Msaa, string ShadowQuality,
    bool Grass, bool DynamicLights, bool WeaponTrails, bool HighQualityTextures,
    bool OptimizeForIntegratedGpu, bool MusicEnabled, int MusicVolume,
    bool EffectsEnabled, int EffectsVolume);

public sealed class GameSettingsService
{
    private readonly string _path;

    public GameSettingsService(string executablePath) =>
        _path = Path.Combine(Path.GetDirectoryName(executablePath)!, "appsettings.local.json");

    public GameSettings Load()
    {
        JsonObject root = LoadRoot();
        JsonObject mu = root["MuOnlineSettings"] as JsonObject ?? new();
        JsonObject graphics = mu["Graphics"] as JsonObject ?? new();
        JsonObject audio = mu["Audio"] as JsonObject ?? new();
        return new(
            Read(graphics, "Width", 1280), Read(graphics, "Height", 720), Read(graphics, "IsFullScreen", false),
            Read(graphics, "QualityPreset", "Auto"), Read(graphics, "VSync", true), Read(graphics, "FrameRateLimit", 60),
            ReadNullable<double>(graphics, "RenderScale"), ReadNullable<bool>(graphics, "Msaa"), Read(graphics, "ShadowQuality", "Off"),
            Read(graphics, "Grass", true), Read(graphics, "DynamicLights", true), Read(graphics, "WeaponTrails", true),
            Read(graphics, "HighQualityTextures", true), Read(graphics, "OptimizeForIntegratedGpu", false),
            Read(audio, "MusicEnabled", true), Read(audio, "MusicVolume", 50), Read(audio, "EffectsEnabled", true), Read(audio, "EffectsVolume", 100));
    }

    public void Save(GameSettings value)
    {
        JsonObject root = LoadRoot();
        JsonObject mu = GetOrCreate(root, "MuOnlineSettings");
        JsonObject graphics = GetOrCreate(mu, "Graphics");
        JsonObject audio = GetOrCreate(mu, "Audio");
        graphics["Width"] = value.Width; graphics["Height"] = value.Height; graphics["IsFullScreen"] = value.Fullscreen;
        graphics["QualityPreset"] = value.QualityPreset; graphics["VSync"] = value.VSync; graphics["FrameRateLimit"] = value.FrameRateLimit;
        graphics["RenderScale"] = value.RenderScale; graphics["Msaa"] = value.Msaa; graphics["ShadowQuality"] = value.ShadowQuality;
        graphics["Grass"] = value.Grass; graphics["DynamicLights"] = value.DynamicLights; graphics["WeaponTrails"] = value.WeaponTrails;
        graphics["HighQualityTextures"] = value.HighQualityTextures; graphics["OptimizeForIntegratedGpu"] = value.OptimizeForIntegratedGpu;
        audio["MusicEnabled"] = value.MusicEnabled; audio["MusicVolume"] = Math.Clamp(value.MusicVolume, 0, 100);
        audio["EffectsEnabled"] = value.EffectsEnabled; audio["EffectsVolume"] = Math.Clamp(value.EffectsVolume, 0, 100);
        Directory.CreateDirectory(Path.GetDirectoryName(_path)!);
        string temporary = _path + ".tmp";
        File.WriteAllText(temporary, root.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        File.Move(temporary, _path, true);
    }

    private JsonObject LoadRoot()
    {
        if (!File.Exists(_path)) return new JsonObject();
        try { return JsonNode.Parse(File.ReadAllText(_path)) as JsonObject ?? new JsonObject(); }
        catch (JsonException) { return new JsonObject(); }
    }

    private static JsonObject GetOrCreate(JsonObject parent, string key)
    {
        if (parent[key] is JsonObject value) return value;
        value = new JsonObject(); parent[key] = value; return value;
    }
    private static T Read<T>(JsonObject node, string key, T fallback) => node[key] is JsonNode value && value.GetValueKind() != JsonValueKind.Null ? value.GetValue<T>() : fallback;
    private static T? ReadNullable<T>(JsonObject node, string key) where T : struct => node[key] is JsonNode value && value.GetValueKind() != JsonValueKind.Null ? value.GetValue<T>() : null;
}
