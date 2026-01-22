using TrapValueGame.Models;

namespace TrapValueGame.Services;

public enum GameState
{
    Loading,
    Analyzing,
    Revealing,
    Result,
    Error
}

public class GameStateService
{
    private readonly GameService _gameService;
    private readonly LocalStorageService _localStorageService;
    private readonly ILogger<GameStateService> _logger;

    public GameState CurrentState { get; private set; } = GameState.Loading;
    public SnapshotData? CurrentSnapshot { get; private set; }
    public RevealData? CurrentReveal { get; private set; }
    public string? PlayerChoice { get; private set; }
    public string? ErrorMessage { get; private set; }

    // Track played snapshots - now backed by localStorage
    private List<int> _playedSnapshotIds = [];

    // Session stats (not persisted - resets on refresh)
    public int TotalPlayed { get; private set; }
    public int CorrectGuesses { get; private set; }

    // Total historical plays (from localStorage)
    public int TotalHistoricalPlays => _playedSnapshotIds.Count;

    public bool IsInitialized { get; private set; }

    public event Action? OnStateChanged;

    public GameStateService(
        GameService gameService,
        LocalStorageService localStorageService,
        ILogger<GameStateService> logger)
    {
        _gameService = gameService;
        _localStorageService = localStorageService;
        _logger = logger;
    }

    /// <summary>
    /// Initialize the service with persisted data from localStorage.
    /// Must be called from OnAfterRenderAsync(firstRender: true).
    /// </summary>
    public async Task InitializeAsync()
    {
        if (IsInitialized) return;

        // Initialize localStorage service first
        await _localStorageService.InitializeAsync();

        // Load persisted IDs
        var persistedIds = _localStorageService.GetPlayedSnapshotIds();
        _playedSnapshotIds = persistedIds.ToList();

        IsInitialized = true;

        _logger.LogInformation("GameStateService initialized with {Count} persisted snapshot IDs",
            _playedSnapshotIds.Count);
    }

    public async Task LoadNextSnapshotAsync()
    {
        // Ensure initialized before loading
        if (!IsInitialized)
        {
            _logger.LogWarning("LoadNextSnapshotAsync called before initialization");
            return;
        }

        try
        {
            CurrentState = GameState.Loading;
            ErrorMessage = null;
            NotifyStateChanged();

            var excludeIds = _playedSnapshotIds.Count > 0 ? _playedSnapshotIds.ToArray() : null;
            var snapshot = await _gameService.GetNextSnapshotAsync(excludeIds: excludeIds);

            if (snapshot == null)
            {
                CurrentState = GameState.Error;
                ErrorMessage = _playedSnapshotIds.Count > 0
                    ? "You've played all available snapshots! Reset your history to play again."
                    : "No snapshots available. Please seed the database first.";
                NotifyStateChanged();
                return;
            }

            CurrentSnapshot = snapshot;
            CurrentReveal = null;
            PlayerChoice = null;
            CurrentState = GameState.Analyzing;

            _logger.LogInformation("Loaded snapshot {SnapshotId}: {FakeName} ({Year})",
                snapshot.SnapshotId, snapshot.FakeName, snapshot.SnapshotYear);

            NotifyStateChanged();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load next snapshot");
            CurrentState = GameState.Error;
            ErrorMessage = "Failed to load game data. Is the API running?";
            NotifyStateChanged();
        }
    }

    public async Task MakeDecisionAsync(string choice)
    {
        if (CurrentSnapshot == null || CurrentState != GameState.Analyzing)
            return;

        if (choice is not ("value" or "trap"))
        {
            _logger.LogWarning("Invalid choice: {Choice}", choice);
            return;
        }

        try
        {
            PlayerChoice = choice;
            CurrentState = GameState.Revealing;
            NotifyStateChanged();

            // Add a small delay for dramatic effect
            await Task.Delay(1500);

            var reveal = await _gameService.RevealOutcomeAsync(CurrentSnapshot.SnapshotId, choice);

            if (reveal == null)
            {
                CurrentState = GameState.Error;
                ErrorMessage = "Failed to reveal outcome.";
                NotifyStateChanged();
                return;
            }

            CurrentReveal = reveal;

            // Add to local list and persist to localStorage
            _playedSnapshotIds.Add(CurrentSnapshot.SnapshotId);
            await _localStorageService.SavePlayedSnapshotIdAsync(CurrentSnapshot.SnapshotId);

            // Update session stats
            TotalPlayed++;
            if (reveal.IsCorrect)
                CorrectGuesses++;

            CurrentState = GameState.Result;

            _logger.LogInformation("Revealed: {Ticker} - {Outcome}, Player was {Correct}",
                reveal.Ticker, reveal.OutcomeLabel, reveal.IsCorrect ? "correct" : "wrong");

            NotifyStateChanged();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to reveal outcome");
            CurrentState = GameState.Error;
            ErrorMessage = "Failed to reveal outcome. Please try again.";
            NotifyStateChanged();
        }
    }

    public async Task PlayAgainAsync()
    {
        await LoadNextSnapshotAsync();
    }

    /// <summary>
    /// Reset session stats only (keeps history).
    /// </summary>
    public void ResetSession()
    {
        TotalPlayed = 0;
        CorrectGuesses = 0;
        CurrentSnapshot = null;
        CurrentReveal = null;
        PlayerChoice = null;
        CurrentState = GameState.Loading;
        NotifyStateChanged();
    }

    /// <summary>
    /// Clear all played history from localStorage.
    /// </summary>
    public async Task ResetHistoryAsync()
    {
        await _localStorageService.ClearPlayedSnapshotIdsAsync();
        _playedSnapshotIds.Clear();
        ResetSession();

        _logger.LogInformation("History cleared - all snapshots available again");
    }

    public double GetAccuracy()
    {
        return TotalPlayed > 0 ? (double)CorrectGuesses / TotalPlayed * 100 : 0;
    }

    private void NotifyStateChanged() => OnStateChanged?.Invoke();
}
