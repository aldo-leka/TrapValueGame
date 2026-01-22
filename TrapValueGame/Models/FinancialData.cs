using System.Text.Json.Serialization;

namespace TrapValueGame.Models;

public class FinancialData
{
    [JsonPropertyName("fiscal_year")]
    public int FiscalYear { get; set; }

    [JsonPropertyName("revenue")]
    public decimal? Revenue { get; set; }

    [JsonPropertyName("gross_margin")]
    public decimal? GrossMargin { get; set; }

    [JsonPropertyName("operating_income")]
    public decimal? OperatingIncome { get; set; }

    [JsonPropertyName("ebitda")]
    public decimal? Ebitda { get; set; }

    [JsonPropertyName("net_income")]
    public decimal? NetIncome { get; set; }

    [JsonPropertyName("free_cash_flow")]
    public decimal? FreeCashFlow { get; set; }

    [JsonPropertyName("total_debt")]
    public decimal? TotalDebt { get; set; }

    [JsonPropertyName("cash_and_equivalents")]
    public decimal? CashAndEquivalents { get; set; }
}
