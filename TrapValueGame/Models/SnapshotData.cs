using System.Text.Json.Serialization;

namespace TrapValueGame.Models;

public class SnapshotData
{
    [JsonPropertyName("snapshot_id")]
    public int SnapshotId { get; set; }

    [JsonPropertyName("fake_name")]
    public string FakeName { get; set; } = string.Empty;

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("industry")]
    public string? Industry { get; set; }

    [JsonPropertyName("snapshot_date")]
    public DateTime SnapshotDate { get; set; }

    [JsonPropertyName("snapshot_year")]
    public int SnapshotYear { get; set; }

    [JsonPropertyName("financials")]
    public List<FinancialData> Financials { get; set; } = [];

    [JsonPropertyName("narrative")]
    public string? Narrative { get; set; }
}
