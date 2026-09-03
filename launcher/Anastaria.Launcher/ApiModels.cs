using System.Text.Json.Serialization;

namespace Anastaria.Launcher;

public sealed record ServerStatus(
    string Status,
    [property: JsonPropertyName("players_online")] int? PlayersOnline,
    int? Season,
    int? Episode);

public sealed record NewsResponse(string Status, IReadOnlyList<NewsArticle> Items);
public sealed record NewsArticle(int Id, string Title, string? Summary, string Category);

public sealed record EventsResponse(string Status, IReadOnlyList<GameEvent> Items);
public sealed record GameEvent(int Id, string Slug, string Schedule, string Timezone, string Category);

public sealed record CommerceCatalog(string Status, IReadOnlyList<ShopProduct> Products);
public sealed record ShopProduct(int Id, string Title, string? Description,
    [property: JsonPropertyName("price_amount")] int PriceAmount,
    [property: JsonPropertyName("currency_code")] string CurrencyCode);

public sealed record LoginRequest(string Username, string Password);
public sealed record LoginResponse(string Status);
