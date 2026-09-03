using System.Net;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace Anastaria.Launcher;

public sealed class AnastariaApiClient : IDisposable
{
    private readonly HttpClient _httpClient;

    public AnastariaApiClient(Uri apiBaseUrl)
    {
        var handler = new HttpClientHandler
        {
            CookieContainer = new CookieContainer(),
            UseCookies = true,
        };
        _httpClient = new HttpClient(handler) { BaseAddress = apiBaseUrl, Timeout = TimeSpan.FromSeconds(8) };
    }

    public Task<ServerStatus?> GetStatusAsync(CancellationToken token) =>
        _httpClient.GetFromJsonAsync<ServerStatus>("server/status", token);

    public Task<NewsResponse?> GetNewsAsync(CancellationToken token) =>
        _httpClient.GetFromJsonAsync<NewsResponse>("news", token);

    public Task<EventsResponse?> GetEventsAsync(CancellationToken token) =>
        _httpClient.GetFromJsonAsync<EventsResponse>("events", token);

    public Task<CommerceCatalog?> GetShopAsync(CancellationToken token) =>
        _httpClient.GetFromJsonAsync<CommerceCatalog>("commerce/catalog", token);

    public async Task LoginAsync(string username, string password, CancellationToken token)
    {
        using HttpResponseMessage response = await _httpClient.PostAsJsonAsync(
            "auth/login", new LoginRequest(username, password), token);
        if (response.IsSuccessStatusCode)
        {
            return;
        }

        string message = "Autentificarea a eșuat.";
        try
        {
            using JsonDocument error = JsonDocument.Parse(await response.Content.ReadAsStringAsync(token));
            if (error.RootElement.TryGetProperty("detail", out JsonElement detail))
            {
                message = detail.GetString() ?? message;
            }
        }
        catch (JsonException)
        {
        }

        throw new HttpRequestException(message);
    }

    public void Dispose() => _httpClient.Dispose();
}
