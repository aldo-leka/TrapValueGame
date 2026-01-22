using Microsoft.JSInterop;

namespace TrapValueGame.Services;

public class LocalStorageService : IAsyncDisposable
{
    private readonly IJSRuntime _jsRuntime;
    private readonly ILogger<LocalStorageService> _logger;

    private const int MaxStoredIds = 1000;

    // Cached IDs to avoid repeated JS calls
    private List<int>? _cachedIds;

    public bool IsInitialized { get; private set; }

    public LocalStorageService(IJSRuntime jsRuntime, ILogger<LocalStorageService> logger)
    {
        _jsRuntime = jsRuntime;
        _logger = logger;
    }

    /// <summary>
    /// Initialize the service by loading persisted IDs from localStorage.
    /// Must be called from OnAfterRenderAsync(firstRender: true).
    /// </summary>
    public async Task InitializeAsync()
    {
        if (IsInitialized) return;

        try
        {
            var ids = await _jsRuntime.InvokeAsync<int[]>("trapValueStorage.getPlayedIds");
            _cachedIds = ids?.ToList() ?? [];
            IsInitialized = true;

            _logger.LogInformation("Loaded {Count} played snapshot IDs from localStorage", _cachedIds.Count);
        }
        catch (JSException ex)
        {
            _logger.LogWarning(ex, "Failed to load from localStorage, starting fresh");
            _cachedIds = [];
            IsInitialized = true;
        }
    }

    /// <summary>
    /// Get all played snapshot IDs.
    /// </summary>
    public int[] GetPlayedSnapshotIds()
    {
        if (!IsInitialized)
        {
            _logger.LogWarning("GetPlayedSnapshotIds called before initialization");
            return [];
        }
        return _cachedIds?.ToArray() ?? [];
    }

    /// <summary>
    /// Save a newly played snapshot ID to localStorage.
    /// </summary>
    public async Task SavePlayedSnapshotIdAsync(int snapshotId)
    {
        if (!IsInitialized)
        {
            _logger.LogWarning("SavePlayedSnapshotIdAsync called before initialization");
            return;
        }

        try
        {
            // Update local cache first
            _cachedIds ??= [];
            if (!_cachedIds.Contains(snapshotId))
            {
                _cachedIds.Add(snapshotId);

                // Enforce limit locally (FIFO - remove oldest)
                if (_cachedIds.Count > MaxStoredIds)
                {
                    _cachedIds = _cachedIds.Skip(_cachedIds.Count - MaxStoredIds).ToList();
                }
            }

            // Persist to localStorage
            await _jsRuntime.InvokeVoidAsync("trapValueStorage.savePlayedId", snapshotId);

            _logger.LogDebug("Saved snapshot ID {Id} to localStorage (total: {Count})",
                snapshotId, _cachedIds.Count);
        }
        catch (JSException ex)
        {
            _logger.LogError(ex, "Failed to save snapshot ID {Id} to localStorage", snapshotId);
        }
    }

    /// <summary>
    /// Clear all played snapshot IDs (reset history).
    /// </summary>
    public async Task ClearPlayedSnapshotIdsAsync()
    {
        try
        {
            await _jsRuntime.InvokeVoidAsync("trapValueStorage.clearPlayedIds");
            _cachedIds?.Clear();

            _logger.LogInformation("Cleared all played snapshot IDs from localStorage");
        }
        catch (JSException ex)
        {
            _logger.LogError(ex, "Failed to clear localStorage");
        }
    }

    /// <summary>
    /// Get count of played snapshots.
    /// </summary>
    public int GetPlayedCount()
    {
        return _cachedIds?.Count ?? 0;
    }

    public ValueTask DisposeAsync()
    {
        _cachedIds = null;
        return ValueTask.CompletedTask;
    }
}
