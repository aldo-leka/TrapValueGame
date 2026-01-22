namespace TrapValueGame.Models;

public enum NarrativeDisplayState
{
    /// <summary>No API key configured - show prompt to configure.</summary>
    NoApiKey,

    /// <summary>Generating narrative - show loading skeleton.</summary>
    Loading,

    /// <summary>Narrative ready - display with typewriter effect.</summary>
    Ready,

    /// <summary>Generation failed - show error alert.</summary>
    Error
}
