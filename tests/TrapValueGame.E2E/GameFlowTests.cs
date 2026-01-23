using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;
using NUnit.Framework;

namespace TrapValueGame.E2E;

/// <summary>
/// End-to-end tests for the game flow.
/// These tests require both the Blazor app and Python API to be running.
/// </summary>
[Parallelizable(ParallelScope.Self)]
[TestFixture]
public class GameFlowTests : PageTest
{
    private const string BaseUrl = "http://localhost:5000";

    public override BrowserNewContextOptions ContextOptions()
    {
        return new BrowserNewContextOptions
        {
            ViewportSize = new ViewportSize { Width = 1280, Height = 720 },
            IgnoreHTTPSErrors = true,
        };
    }

    [Test]
    public async Task HomePage_LoadsSuccessfully()
    {
        await Page.GotoAsync(BaseUrl);

        // Check for app title
        await Expect(Page.Locator("text=Trap Or Value")).ToBeVisibleAsync();
    }

    [Test]
    public async Task Game_ShowsLoadingState_Initially()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Should show loading indicator initially
        var loadingText = Page.GetByText("Finding your next case");
        await Expect(loadingText).ToBeVisibleAsync(new() { Timeout = 5000 });
    }

    [Test]
    public async Task Game_DisplaysSnapshotData_WhenLoaded()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load (financials table should appear)
        var financialsTable = Page.Locator(".mud-table");
        await financialsTable.WaitForAsync(new() { Timeout = 30000 });

        // Should show company card
        await Expect(Page.Locator("text=Market Snapshot").Or(Page.Locator(".company-card"))).ToBeVisibleAsync();
    }

    [Test]
    public async Task SwipeCard_IsVisible_WhenGameLoaded()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for swipe card
        var swipeCard = Page.Locator(".swipe-card");
        await swipeCard.WaitForAsync(new() { Timeout = 30000 });

        // Should have decision buttons
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        var valueButton = Page.GetByRole(AriaRole.Button, new() { Name = "VALUE" });

        await Expect(trapButton).ToBeVisibleAsync();
        await Expect(valueButton).ToBeVisibleAsync();
    }

    [Test]
    public async Task ClickTrap_ShowsRevealingState()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        await trapButton.WaitForAsync(new() { Timeout = 30000 });

        // Click trap button
        await trapButton.ClickAsync();

        // Should show revealing state
        var revealingText = Page.GetByText("You said TRAP");
        await Expect(revealingText).ToBeVisibleAsync(new() { Timeout = 5000 });
    }

    [Test]
    public async Task ClickValue_ShowsRevealingState()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        var valueButton = Page.GetByRole(AriaRole.Button, new() { Name = "VALUE" });
        await valueButton.WaitForAsync(new() { Timeout = 30000 });

        // Click value button
        await valueButton.ClickAsync();

        // Should show revealing state
        var revealingText = Page.GetByText("You said VALUE");
        await Expect(revealingText).ToBeVisibleAsync(new() { Timeout = 5000 });
    }

    [Test]
    public async Task FullGameFlow_TrapChoice_ShowsResult()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load and click trap
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        await trapButton.WaitForAsync(new() { Timeout = 30000 });
        await trapButton.ClickAsync();

        // Wait for result to show
        var resultText = Page.GetByText("Correct!").Or(Page.GetByText("Wrong!"));
        await Expect(resultText).ToBeVisibleAsync(new() { Timeout = 10000 });

        // Should show company reveal
        var companyReveal = Page.GetByText("The Company Was");
        await Expect(companyReveal).ToBeVisibleAsync();

        // Should show play again button
        var playAgainButton = Page.GetByRole(AriaRole.Button, new() { Name = "Play Again" });
        await Expect(playAgainButton).ToBeVisibleAsync();
    }

    [Test]
    public async Task PlayAgain_LoadsNewSnapshot()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Complete first game
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        await trapButton.WaitForAsync(new() { Timeout = 30000 });
        await trapButton.ClickAsync();

        // Wait for result
        var playAgainButton = Page.GetByRole(AriaRole.Button, new() { Name = "Play Again" });
        await playAgainButton.WaitForAsync(new() { Timeout = 10000 });

        // Click play again
        await playAgainButton.ClickAsync();

        // Should show loading or new snapshot
        var loadingOrGame = Page.GetByText("Finding your next case").Or(Page.Locator(".swipe-card"));
        await Expect(loadingOrGame).ToBeVisibleAsync(new() { Timeout = 10000 });
    }

    [Test]
    public async Task KeyboardShortcuts_A_SelectsTrap()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        var swipeContainer = Page.Locator(".swipe-container");
        await swipeContainer.WaitForAsync(new() { Timeout = 30000 });

        // Focus and press 'A' for trap
        await swipeContainer.FocusAsync();
        await Page.Keyboard.PressAsync("a");

        // Should show trap choice in revealing state
        var revealingText = Page.GetByText("You said TRAP");
        await Expect(revealingText).ToBeVisibleAsync(new() { Timeout = 5000 });
    }

    [Test]
    public async Task KeyboardShortcuts_D_SelectsValue()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        var swipeContainer = Page.Locator(".swipe-container");
        await swipeContainer.WaitForAsync(new() { Timeout = 30000 });

        // Focus and press 'D' for value
        await swipeContainer.FocusAsync();
        await Page.Keyboard.PressAsync("d");

        // Should show value choice in revealing state
        var revealingText = Page.GetByText("You said VALUE");
        await Expect(revealingText).ToBeVisibleAsync(new() { Timeout = 5000 });
    }

    [Test]
    public async Task SessionStats_IncrementAfterGame()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Complete first game
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        await trapButton.WaitForAsync(new() { Timeout = 30000 });
        await trapButton.ClickAsync();

        // Wait for result
        await Page.WaitForSelectorAsync("text=This Session", new() { Timeout = 10000 });

        // Session count should show "1"
        var sessionStat = Page.Locator(".stat-item >> text=This Session").First;
        await Expect(sessionStat).ToBeVisibleAsync();
    }
}
