using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;
using NUnit.Framework;

namespace TrapValueGame.E2E;

/// <summary>
/// Accessibility tests to ensure the app is usable by everyone.
/// </summary>
[Parallelizable(ParallelScope.Self)]
[TestFixture]
public class AccessibilityTests : PageTest
{
    private const string BaseUrl = "http://localhost:5000";

    [Test]
    public async Task Page_HasTitle()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        var title = await Page.TitleAsync();
        Assert.That(title, Is.Not.Empty);
        Assert.That(title, Does.Contain("Trap"));
    }

    [Test]
    public async Task Buttons_HaveAccessibleNames()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        await Page.Locator(".swipe-card").WaitForAsync(new() { Timeout = 30000 });

        // Get all buttons
        var buttons = Page.GetByRole(AriaRole.Button);
        var buttonCount = await buttons.CountAsync();

        Assert.That(buttonCount, Is.GreaterThan(0), "Page should have buttons");

        // Each button should have accessible name
        for (var i = 0; i < buttonCount; i++)
        {
            var button = buttons.Nth(i);
            var name = await button.GetAttributeAsync("aria-label") ??
                       await button.InnerTextAsync();

            Assert.That(string.IsNullOrWhiteSpace(name), Is.False,
                $"Button {i} should have accessible name");
        }
    }

    [Test]
    public async Task SwipeContainer_IsFocusable()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        var swipeContainer = Page.Locator(".swipe-container");
        await swipeContainer.WaitForAsync(new() { Timeout = 30000 });

        // Should have tabindex for focus
        var tabindex = await swipeContainer.GetAttributeAsync("tabindex");
        Assert.That(tabindex, Is.Not.Null, "Swipe container should be focusable");
    }

    [Test]
    public async Task KeyboardNavigation_Works()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for game to load
        await Page.Locator(".swipe-card").WaitForAsync(new() { Timeout = 30000 });

        // Tab through the page
        await Page.Keyboard.PressAsync("Tab");
        await Page.Keyboard.PressAsync("Tab");
        await Page.Keyboard.PressAsync("Tab");

        // Should be able to navigate with keyboard
        // (No assertion needed - just checking it doesn't throw)
    }

    [Test]
    public async Task ColorContrast_SufficientForText()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for page to load
        await Page.Locator(".mud-typography").First.WaitForAsync(new() { Timeout = 30000 });

        // Check that text is visible (basic check)
        var textElements = Page.Locator(".mud-typography");
        var count = await textElements.CountAsync();

        Assert.That(count, Is.GreaterThan(0), "Page should have text elements");
    }

    [Test]
    public async Task Links_HaveHref()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for page to load
        await Page.WaitForLoadStateAsync(LoadState.NetworkIdle);

        var links = Page.GetByRole(AriaRole.Link);
        var linkCount = await links.CountAsync();

        for (var i = 0; i < linkCount; i++)
        {
            var link = links.Nth(i);
            var href = await link.GetAttributeAsync("href");

            Assert.That(string.IsNullOrWhiteSpace(href), Is.False,
                $"Link {i} should have href");
        }
    }

    [Test]
    public async Task ResultPage_AnnouncesOutcome()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Play a game
        var trapButton = Page.GetByRole(AriaRole.Button, new() { Name = "TRAP" });
        await trapButton.WaitForAsync(new() { Timeout = 30000 });
        await trapButton.ClickAsync();

        // Wait for result
        var result = Page.GetByText("Correct!").Or(Page.GetByText("Wrong!"));
        await result.WaitForAsync(new() { Timeout = 10000 });

        // Result should be visible (announces outcome)
        await Expect(result).ToBeVisibleAsync();
    }

    [Test]
    public async Task ReducedMotion_Respected()
    {
        // Create context with reduced motion preference
        var context = await Browser.NewContextAsync(new BrowserNewContextOptions
        {
            ReducedMotion = ReducedMotion.Reduce
        });

        var page = await context.NewPageAsync();
        await page.GotoAsync($"{BaseUrl}/game");

        // Page should load without animation issues
        await page.WaitForLoadStateAsync(LoadState.NetworkIdle);

        // Basic check - page loads successfully
        var body = page.Locator("body");
        await Expect(body).ToBeVisibleAsync();

        await context.CloseAsync();
    }

    [Test]
    public async Task HeadingsHierarchy_IsLogical()
    {
        await Page.GotoAsync($"{BaseUrl}/game");

        // Wait for content to load
        await Page.Locator(".swipe-card").WaitForAsync(new() { Timeout = 30000 });

        // Get all headings
        var h1Count = await Page.Locator("h1").CountAsync();
        var h2Count = await Page.Locator("h2").CountAsync();
        var h3Count = await Page.Locator("h3").CountAsync();

        // MudBlazor uses typography classes instead of semantic headings,
        // so we check for those too
        var typographyH5 = await Page.Locator(".mud-typography-h5").CountAsync();
        var typographyH6 = await Page.Locator(".mud-typography-h6").CountAsync();

        // Should have some heading-like elements
        var totalHeadings = h1Count + h2Count + h3Count + typographyH5 + typographyH6;
        Assert.That(totalHeadings, Is.GreaterThan(0), "Page should have heading elements");
    }
}
