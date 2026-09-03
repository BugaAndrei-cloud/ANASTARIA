using System.Buffers;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;

namespace Anastaria.Launcher;

public sealed record PatchManifestEnvelope(string Payload, string Signature);
public sealed record PatchManifest(string Version, IReadOnlyList<PatchFile> Files);
public sealed record PatchFile(string Path, Uri Url, string Sha256, long Size);
public sealed record PatchProgress(string FileName, int CompletedFiles, int TotalFiles, long CompletedBytes, long TotalBytes, double BytesPerSecond)
{
    public double Fraction => TotalBytes <= 0 ? 0 : Math.Clamp(CompletedBytes / (double)TotalBytes, 0, 1);
}

public sealed class PatchService : IDisposable
{
    private const int BufferSize = 128 * 1024;
    private readonly HttpClient _httpClient = new() { Timeout = TimeSpan.FromMinutes(30) };

    public async Task<string> VerifyAndRepairAsync(Uri manifestUrl, string installationDirectory, string publicKeyPem,
        IProgress<PatchProgress> progress, CancellationToken token)
    {
        ValidateRemoteUri(manifestUrl, nameof(manifestUrl));
        byte[] envelopeBytes = await _httpClient.GetByteArrayAsync(manifestUrl, token);
        PatchManifestEnvelope envelope = JsonSerializer.Deserialize<PatchManifestEnvelope>(envelopeBytes, JsonOptions)
            ?? throw new InvalidDataException("Invalid patch manifest envelope.");
        byte[] payload = DecodeBase64(envelope.Payload, "manifest payload");
        byte[] signature = DecodeBase64(envelope.Signature, "manifest signature");
        VerifySignature(payload, signature, publicKeyPem);
        PatchManifest manifest = JsonSerializer.Deserialize<PatchManifest>(payload, JsonOptions)
            ?? throw new InvalidDataException("Invalid patch manifest payload.");

        string root = Path.GetFullPath(installationDirectory).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        Directory.CreateDirectory(root);
        EnsureDirectoryIsSafe(root);
        IReadOnlyList<ValidatedPatchFile> files = ValidateFiles(manifest.Files, root);
        long totalBytes = files.Sum(file => file.Source.Size);
        long completedBytes = 0;
        int completedFiles = 0;

        foreach (ValidatedPatchFile file in files)
        {
            token.ThrowIfCancellationRequested();
            if (await HasExpectedFileAsync(file.Destination, file.Source.Size, file.Source.Sha256, token))
            {
                completedBytes += file.Source.Size;
                progress.Report(new(file.Source.Path, ++completedFiles, files.Count, completedBytes, totalBytes, 0));
                continue;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(file.Destination)!);
            EnsureDirectoryIsSafe(Path.GetDirectoryName(file.Destination)!);
            string staging = file.Destination + ".anastaria-download";
            TryDelete(staging);
            var stopwatch = Stopwatch.StartNew();
            long fileBytes = 0;
            try
            {
                using HttpResponseMessage response = await _httpClient.GetAsync(file.Source.Url, HttpCompletionOption.ResponseHeadersRead, token);
                response.EnsureSuccessStatusCode();
                if (response.Content.Headers.ContentLength is long length && length != file.Source.Size)
                    throw new InvalidDataException($"Unexpected download size for {file.Source.Path}.");
                await using Stream source = await response.Content.ReadAsStreamAsync(token);
                await using FileStream target = new(staging, FileMode.CreateNew, FileAccess.Write, FileShare.None, BufferSize, FileOptions.Asynchronous | FileOptions.SequentialScan);
                byte[] buffer = ArrayPool<byte>.Shared.Rent(BufferSize);
                try
                {
                    int read;
                    while ((read = await source.ReadAsync(buffer.AsMemory(0, BufferSize), token)) > 0)
                    {
                        fileBytes += read;
                        if (fileBytes > file.Source.Size) throw new InvalidDataException($"Download exceeds declared size for {file.Source.Path}.");
                        await target.WriteAsync(buffer.AsMemory(0, read), token);
                        progress.Report(new(file.Source.Path, completedFiles, files.Count, completedBytes + fileBytes, totalBytes,
                            fileBytes / Math.Max(.1, stopwatch.Elapsed.TotalSeconds)));
                    }
                    await target.FlushAsync(token);
                }
                finally { ArrayPool<byte>.Shared.Return(buffer); }

                if (!await HasExpectedFileAsync(staging, file.Source.Size, file.Source.Sha256, token))
                    throw new InvalidDataException($"Hash or size mismatch for {file.Source.Path}.");
                File.Move(staging, file.Destination, true);
            }
            catch { TryDelete(staging); throw; }

            completedBytes += file.Source.Size;
            progress.Report(new(file.Source.Path, ++completedFiles, files.Count, completedBytes, totalBytes, 0));
        }

        await File.WriteAllTextAsync(Path.Combine(root, ".anastaria-version"), manifest.Version, token);
        return manifest.Version;
    }

    private static IReadOnlyList<ValidatedPatchFile> ValidateFiles(IReadOnlyList<PatchFile> source, string root)
    {
        var result = new List<ValidatedPatchFile>(source.Count);
        var destinations = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (PatchFile file in source)
        {
            if (string.IsNullOrWhiteSpace(file.Path) || Path.IsPathRooted(file.Path) || file.Size < 0 || file.Sha256.Length != 64 || !file.Sha256.All(Uri.IsHexDigit))
                throw new InvalidDataException($"Invalid patch entry: {file.Path}.");
            ValidateRemoteUri(file.Url, file.Path);
            string destination = Path.GetFullPath(Path.Combine(root, file.Path.Replace('/', Path.DirectorySeparatorChar)));
            if (!destination.StartsWith(root, StringComparison.OrdinalIgnoreCase) || !destinations.Add(destination))
                throw new InvalidDataException($"Unsafe or duplicate patch path: {file.Path}.");
            result.Add(new(file, destination));
        }
        return result;
    }

    private static void ValidateRemoteUri(Uri uri, string name)
    {
        bool localDevelopment = uri.IsLoopback && uri.Scheme == Uri.UriSchemeHttp;
        if (!uri.IsAbsoluteUri || (uri.Scheme != Uri.UriSchemeHttps && !localDevelopment))
            throw new InvalidDataException($"HTTPS is required for {name}.");
    }

    private static void EnsureDirectoryIsSafe(string directory)
    {
        for (DirectoryInfo? current = new(directory); current is not null; current = current.Parent)
            if (current.Exists && current.Attributes.HasFlag(FileAttributes.ReparsePoint))
                throw new InvalidDataException($"Patch directory cannot contain links: {current.FullName}.");
    }

    private static void VerifySignature(byte[] payload, byte[] signature, string publicKeyPem)
    {
        if (string.IsNullOrWhiteSpace(publicKeyPem)) throw new InvalidDataException("Patch signing public key is not configured.");
        using RSA rsa = RSA.Create();
        rsa.ImportFromPem(publicKeyPem);
        if (!rsa.VerifyData(payload, signature, HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
            throw new InvalidDataException("Patch manifest signature is invalid.");
    }

    private static byte[] DecodeBase64(string value, string name)
    {
        try { return Convert.FromBase64String(value); }
        catch (FormatException ex) { throw new InvalidDataException($"Invalid {name}.", ex); }
    }

    private static async Task<bool> HasExpectedFileAsync(string path, long size, string expectedHash, CancellationToken token)
    {
        var info = new FileInfo(path);
        if (!info.Exists || info.Length != size || info.Attributes.HasFlag(FileAttributes.ReparsePoint)) return false;
        await using FileStream stream = new(path, FileMode.Open, FileAccess.Read, FileShare.Read, BufferSize, FileOptions.Asynchronous | FileOptions.SequentialScan);
        byte[] hash = await SHA256.HashDataAsync(stream, token);
        return CryptographicOperations.FixedTimeEquals(hash, Convert.FromHexString(expectedHash));
    }

    private static void TryDelete(string path) { if (File.Exists(path)) File.Delete(path); }
    public void Dispose() => _httpClient.Dispose();
    private sealed record ValidatedPatchFile(PatchFile Source, string Destination);
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
}
