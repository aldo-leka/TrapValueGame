using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;
using NUnit.Framework;

namespace TrapValueGame.E2E;

/// <summary>
/// End-to-end tests for settings and API key configuration.
/// </summary>
[Parallelizable(ParallelScope.Self)]
[TestFixture]
public class SettingsTests : PageTest
{
    private const string BaseUrl = "http://localhost:5000";

    [Test]
    public async Task SettingsButton_OpensDialog()
    {
        await Page.GotoAsync(BaseUrl);

        // Find and click settings button
        var settingsButton = Page.Locator("[aria-label='Settings']").Or(
            Page.Locator("button").Filter(new() { Has = Page.Locator("svg") }).Last
        );

        await settingsButton.ClickAsync();

        // Dialog should appear
        var dialog = Page.Locator(".mud-dialog");
        await Expect(dialog).ToBeVisibleAsync(new() { Timeout = 5000 });

        // Should show API key input
        var apiKeyLabel = Page.GetByText("Gemini API Key");
        await Expect(apiKeyLabel).ToBeVisibleAsync();
    }

    [Test]
    public async Task ApiKeyDialog_HasTestConnectionButton()
    {
        await Page.GotoAsync(BaseUrl);

        // Open settings
        var settingsButton = Page.Locator("button").Filter(new() { Has = Page.Locator("svg") }).Last;
        await settingsButton.ClickAsync();

        // Should have test connection button
        var testButton = Page.GetByRole(AriaRole.Button, new() { Name = "Test Connection" });
        await Expect(testButton).ToBeVisibleAsync();
    }

    [Test]
    public async Task ApiKeyDialog_CanBeClosed()
    {
        await Page.GotoAsync(BaseUrl);

        // Open settings
        var settingsButton = Page.Locator("button").Filter(new() { Has = Page.Locator("svg") }).Last;
        await settingsButton.ClickAsync();

        // Close with cancel button
        var cancelButton = Page.GetByRole(AriaRole.Button, new() { Name = "Cancel" });
        await cancelButton.ClickAsync();

        // Dialog should close
        var dialog = Page.Locator(".mud-dialog");
        await Expect(dialog).ToBeHiddenAsync();
    }

    [Test]
    public async Task ApiKeyInput_TogglesVisibility()
    {
        await Page.GotoAsync(BaseUrl);

        // Open settings
        var settingsButton = Page.Locator("button").Filter(new() { Has = Page.Locator("svg") }).Last;
        await settingsButton.ClickAsync();

        // Find input field
        var inputField = Page.Locator("input[type='password']");
        await Expect(inputField).ToBeVisibleAsync();

        // Click visibility toggle
        var toggleButton = Page.Locator(".mud-input-adornment button").First;
        await toggleButton.ClickAsync();

        // Input type should change to text
        var textInput = Page.Locator("input[type='text']").First;
        await Expect(textInput).ToBeVisibleAsync();
    }

    [Test]
    public async Task NarrativePrompt_ShownWithoutApiKey()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        await Page.Locator(".swipe-card").WaitForAsync(new() { Timeout = 30000 });

        // Should show configure settings prompt (no API key by default)
        var configureButton = Page.GetByText("Configure Settings").Or(
            Page.GetByText("AI Analysis Unavailable")
        );

        await Expect(configureButton).ToBeVisibleAsync(new() { Timeout = 5000 });
    }
}
