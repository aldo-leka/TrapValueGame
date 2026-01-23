using System.Net.Http.Json;
using TrapValueGame.Models;

namespace TrapValueGame.Services;

public class GameService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GameService> _logger;
    private readonly NetworkStatusService _networkStatusService;

    public GameService(
        IHttpClientFactory httpClientFactory,
        ILogger<GameService> logger,
        NetworkStatusService networkStatusService)
    {
        _httpClient = httpClientFactory.CreateClient("PythonApi");
        _logger = logger;
        _networkStatusService = networkStatusService;
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

            _networkStatusService.RecordApiSuccess();
            return response;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to fetch next snapshot");
            _networkStatusService.RecordApiError(GetFriendlyErrorMessage(ex));
            throw;
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            _logger.LogError(ex, "Request timed out fetching next snapshot");
            _networkStatusService.RecordApiError("Request timed out");
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

            var result = await response.Content.ReadFromJsonAsync<RevealData>(cancellationToken);
            _networkStatusService.RecordApiSuccess();
            return result;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to reveal outcome for snapshot {SnapshotId}", snapshotId);
            _networkStatusService.RecordApiError(GetFriendlyErrorMessage(ex));
            throw;
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            _logger.LogError(ex, "Request timed out revealing outcome");
            _networkStatusService.RecordApiError("Request timed out");
            throw;
        }
    }

    public async Task<bool> CheckHealthAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetAsync("/health", cancellationToken);
            var isHealthy = response.IsSuccessStatusCode;

            if (isHealthy)
                _networkStatusService.RecordApiSuccess();
            else
                _networkStatusService.RecordApiError($"Health check failed: {response.StatusCode}");

            return isHealthy;
        }
        catch (Exception ex)
        {
            _networkStatusService.RecordApiError(GetFriendlyErrorMessage(ex));
            return false;
        }
    }

    private static string GetFriendlyErrorMessage(Exception ex)
    {
        return ex switch
        {
            HttpRequestException { StatusCode: System.Net.HttpStatusCode.NotFound } =>
                "API endpoint not found",
            HttpRequestException { StatusCode: System.Net.HttpStatusCode.ServiceUnavailable } =>
                "Server is unavailable",
            HttpRequestException { StatusCode: System.Net.HttpStatusCode.InternalServerError } =>
                "Server error occurred",
            HttpRequestException { InnerException: System.Net.Sockets.SocketException } =>
                "Cannot connect to server",
            HttpRequestException =>
                "Network error occurred",
            TaskCanceledException =>
                "Request timed out",
            _ =>
                "An error occurred"
        };
    }
}
