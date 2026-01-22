namespace TrapValueGame.Services;

/// <summary>
/// Stores the user's Gemini API key for the duration of their session.
/// Scoped lifetime = circuit-scoped in Blazor Server (cleared on refresh/disconnect).
/// </summary>
public class ApiKeyService
{
    private string? _apiKey;
    private bool _isValidated;

    /// <summary>True if an API key has been configured.</summary>
    public bool HasApiKey => !string.IsNullOrWhiteSpace(_apiKey);

    /// <summary>True if the API key has been validated against Gemini API.</summary>
    public bool IsValidated => _isValidated;

    public void SetApiKey(string? key)
    {
        _apiKey = key?.Trim();
        _isValidated = false;
    }

    public string? GetApiKey() => _apiKey;

    public void ClearApiKey()
    {
        _apiKey = null;
        _isValidated = false;
    }

    public void MarkValidated() => _isValidated = true;
}
