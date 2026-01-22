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
    private readonly ILogger<GameStateService> _logger;

    public GameState CurrentState { get; private set; } = GameState.Loading;
    public SnapshotData? CurrentSnapshot { get; private set; }
    public RevealData? CurrentReveal { get; private set; }
    public string? PlayerChoice { get; private set; }
    public string? ErrorMessage { get; private set; }

    // Track played snapshots to avoid repeats in a session
    private readonly List<int> _playedSnapshotIds = [];

    // Session stats
    public int TotalPlayed { get; private set; }
    public int CorrectGuesses { get; private set; }

    public event Action? OnStateChanged;

    public GameStateService(GameService gameService, ILogger<GameStateService> logger)
    {
        _gameService = gameService;
        _logger = logger;
    }

    public async Task LoadNextSnapshotAsync()
    {
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
                ErrorMessage = "No snapshots available. Please seed the database first.";
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
            _playedSnapshotIds.Add(CurrentSnapshot.SnapshotId);

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

    public void ResetSession()
    {
        _playedSnapshotIds.Clear();
        TotalPlayed = 0;
        CorrectGuesses = 0;
        CurrentSnapshot = null;
        CurrentReveal = null;
        PlayerChoice = null;
        CurrentState = GameState.Loading;
        NotifyStateChanged();
    }

    public double GetAccuracy()
    {
        return TotalPlayed > 0 ? (double)CorrectGuesses / TotalPlayed * 100 : 0;
    }

    private void NotifyStateChanged() => OnStateChanged?.Invoke();
}
