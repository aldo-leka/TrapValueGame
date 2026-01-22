using System.Net.Http.Json;
using TrapValueGame.Models;

namespace TrapValueGame.Services;

public class GameService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GameService> _logger;

    public GameService(IHttpClientFactory httpClientFactory, ILogger<GameService> logger)
    {
        _httpClient = httpClientFactory.CreateClient("PythonApi");
        _logger = logger;
    }

    public async Task<SnapshotData?> GetNextSnapshotAsync(
        string? difficulty = null,
        string? sector = null,
        int[]? excludeIds = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var queryParams = new List<string>();

            if (!string.IsNullOrEmpty(difficulty))
                queryParams.Add($"difficulty={Uri.EscapeDataString(difficulty)}");

            if (!string.IsNullOrEmpty(sector))
                queryParams.Add($"sector={Uri.EscapeDataString(sector)}");

            if (excludeIds is { Length: > 0 })
                queryParams.Add($"exclude_ids={string.Join(",", excludeIds)}");

            var url = "/game/next";
            if (queryParams.Count > 0)
                url += "?" + string.Join("&", queryParams);

            _logger.LogInformation("Fetching next snapshot from {Url}", url);

            var response = await _httpClient.GetFromJsonAsync<SnapshotData>(url, cancellationToken);
            return response;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to fetch next snapshot");
            throw;
        }
    }

    public async Task<RevealData?> RevealOutcomeAsync(
        int snapshotId,
        string playerChoice,
        CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Revealing outcome for snapshot {SnapshotId} with choice {Choice}",
                snapshotId, playerChoice);

            var response = await _httpClient.PostAsJsonAsync(
                $"/game/reveal/{snapshotId}?player_choice={Uri.EscapeDataString(playerChoice)}",
                new { },
                cancellationToken);

            response.EnsureSuccessStatusCode();

            return await response.Content.ReadFromJsonAsync<RevealData>(cancellationToken);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to reveal outcome for snapshot {SnapshotId}", snapshotId);
            throw;
        }
    }

    public async Task<bool> CheckHealthAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetAsync("/health", cancellationToken);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }
}
