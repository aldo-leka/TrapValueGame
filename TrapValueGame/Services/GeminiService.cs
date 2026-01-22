using Mscc.GenerativeAI;
using TrapValueGame.Models;

namespace TrapValueGame.Services;

public class GeminiService
{
    private readonly ApiKeyService _apiKeyService;
    private readonly ILogger<GeminiService> _logger;

    private const string ModelId = "gemini-3-flash-preview";

    public GeminiService(ApiKeyService apiKeyService, ILogger<GeminiService> logger)
    {
        _apiKeyService = apiKeyService;
        _logger = logger;
    }

    /// <summary>
    /// Generates a narrative for the given snapshot.
    /// Returns null if no API key is configured or generation fails.
    /// </summary>
    public async Task<string?> GenerateNarrativeAsync(
        string sector,
        DateTime snapshotDate,
        List<FinancialData> financials,
        CancellationToken cancellationToken = default)
    {
        var apiKey = _apiKeyService.GetApiKey();
        if (string.IsNullOrWhiteSpace(apiKey))
        {
            _logger.LogDebug("No API key configured, skipping narrative generation");
            return null;
        }

        try
        {
            var prompt = BuildPrompt(sector, snapshotDate, financials);

            var gemini = new GoogleAI(apiKey);
            var model = gemini.GenerativeModel(model: ModelId);

            var response = await model.GenerateContent(prompt);

            _apiKeyService.MarkValidated();
            return response.Text ?? "Analysis unavailable.";
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to generate narrative");
            return null;
        }
    }

    /// <summary>
    /// Tests if the configured API key is valid.
    /// </summary>
    public async Task<(bool Success, string? Error)> TestApiKeyAsync()
    {
        var apiKey = _apiKeyService.GetApiKey();
        if (string.IsNullOrWhiteSpace(apiKey))
            return (false, "No API key configured");

        try
        {
            var gemini = new GoogleAI(apiKey);
            var model = gemini.GenerativeModel(model: ModelId);

            await model.GenerateContent("Say 'OK' if you can read this.");

            _apiKeyService.MarkValidated();
            return (true, null);
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }
    }

    private static string BuildPrompt(string sector, DateTime date, List<FinancialData> financials)
    {
        var year = date.Year;
        var month = date.ToString("MMMM");

        var financialSummary = string.Join("\n", financials.Select(f =>
        {
            var parts = new List<string> { $"- {f.FiscalYear}:" };

            if (f.Revenue.HasValue)
                parts.Add($"Revenue ${f.Revenue.Value:N1}M");
            if (f.NetIncome.HasValue)
                parts.Add($"Net Income ${f.NetIncome.Value:N1}M");
            if (f.FreeCashFlow.HasValue)
                parts.Add($"FCF ${f.FreeCashFlow.Value:N1}M");
            if (f.GrossMargin.HasValue)
                parts.Add($"Gross Margin {f.GrossMargin.Value:P1}");
            if (f.TotalDebt.HasValue)
                parts.Add($"Debt ${f.TotalDebt.Value:N1}M");

            return string.Join(", ", parts);
        }));

        return $"""
            You are a value investing analyst writing in {month} {year}.

            CRITICAL: You must NOT reference any events, news, or developments after {date:MMMM yyyy}.
            Write as if you are living in {month} {year} - you have no knowledge of the future.

            Analyze this {sector} company based on the following financials:
            {financialSummary}

            Write a 3-paragraph analysis:
            1. Current state: Describe the company's financial situation AT THIS TIME ({month} {year})
            2. Bull case: What optimists believe could happen going forward
            3. Bear case: What pessimists fear could happen

            Rules:
            - Do NOT mention the company name, ticker, or any identifying information
            - Use present tense ("The company is..." not "The company was...")
            - Be specific about the numbers you see in the financials
            - Keep it under 200 words total
            - Focus on the financials provided, not external events
            """;
    }
}
