using System.Text.Json.Serialization;

namespace TrapValueGame.Models;

public class RevealData
{
    [JsonPropertyName("ticker")]
    public string Ticker { get; set; } = string.Empty;

    [JsonPropertyName("company_name")]
    public string CompanyName { get; set; } = string.Empty;

    [JsonPropertyName("snapshot_date")]
    public DateTime SnapshotDate { get; set; }

    [JsonPropertyName("price_at_snapshot")]
    public decimal PriceAtSnapshot { get; set; }

    [JsonPropertyName("price_at_24mo")]
    public decimal PriceAt24Mo { get; set; }

    [JsonPropertyName("return_24mo")]
    public decimal Return24Mo { get; set; }

    [JsonPropertyName("outcome_label")]
    public string OutcomeLabel { get; set; } = string.Empty;

    [JsonPropertyName("player_choice")]
    public string PlayerChoice { get; set; } = string.Empty;

    [JsonPropertyName("is_correct")]
    public bool IsCorrect { get; set; }

    [JsonPropertyName("price_series")]
    public List<PricePointDto> PriceSeries { get; set; } = [];
}

public class PricePointDto
{
    [JsonPropertyName("date")]
    public DateTime Date { get; set; }

    [JsonPropertyName("price")]
    public decimal Price { get; set; }
}
