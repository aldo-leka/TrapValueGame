using MudBlazor.Services;
using TrapValueGame.Components;
using TrapValueGame.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddMudServices();

// Add HttpClient for Python API
builder.Services.AddHttpClient("PythonApi", client =>
{
    client.BaseAddress = new Uri(
        builder.Configuration["PythonApiUrl"] ?? "http://localhost:8000"
    );
    client.Timeout = TimeSpan.FromSeconds(30);
});

// Add game services
builder.Services.AddScoped<GameService>();
builder.Services.AddScoped<LocalStorageService>();
builder.Services.AddScoped<GameStateService>();

// Add AI services (session-scoped for API key isolation)
builder.Services.AddScoped<ApiKeyService>();
builder.Services.AddScoped<GeminiService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseStatusCodePagesWithReExecute("/not-found");
app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();