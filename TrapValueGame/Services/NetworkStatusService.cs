using Microsoft.JSInterop;

namespace TrapValueGame.Services;

public class NetworkStatusService : IAsyncDisposable
{
    private readonly IJSRuntime _jsRuntime;
    private readonly ILogger<NetworkStatusService> _logger;
    private DotNetObjectReference<NetworkStatusService>? _dotNetRef;

    public bool IsOnline { get; private set; } = true;
    public bool IsApiHealthy { get; private set; } = true;
    public DateTime? LastSuccessfulApiCall { get; private set; }
    public string? LastApiError { get; private set; }

    public event Action? OnStatusChanged;

    public NetworkStatusService(IJSRuntime jsRuntime, ILogger<NetworkStatusService> logger)
    {
        _jsRuntime = jsRuntime;
        _logger = logger;
    }

    public async Task InitializeAsync()
    {
        try
        {
            _dotNetRef = DotNetObjectReference.Create(this);

            // Register for online/offline events via JS interop
            await _jsRuntime.InvokeVoidAsync("eval", $@"
                window.networkStatusHandler = {{
                    dotNetRef: null,
                    init: function(ref) {{
                        this.dotNetRef = ref;
                        window.addEventListener('online', () => this.dotNetRef.invokeMethodAsync('OnOnlineStatusChanged', true));
                        window.addEventListener('offline', () => this.dotNetRef.invokeMethodAsync('OnOnlineStatusChanged', false));
                    }}
                }};
            ");

            await _jsRuntime.InvokeVoidAsync("networkStatusHandler.init", _dotNetRef);

            // Check initial status
            IsOnline = await _jsRuntime.InvokeAsync<bool>("eval", "navigator.onLine");

            _logger.LogInformation("NetworkStatusService initialized. Online: {IsOnline}", IsOnline);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to initialize network status monitoring");
            // Assume online if JS interop fails
            IsOnline = true;
        }
    }

    [JSInvokable]
    public void OnOnlineStatusChanged(bool isOnline)
    {
        if (IsOnline != isOnline)
        {
            IsOnline = isOnline;
            _logger.LogInformation("Network status changed. Online: {IsOnline}", IsOnline);
            OnStatusChanged?.Invoke();
        }
    }

    public void RecordApiSuccess()
    {
        LastSuccessfulApiCall = DateTime.UtcNow;
        LastApiError = null;
        if (!IsApiHealthy)
        {
            IsApiHealthy = true;
            OnStatusChanged?.Invoke();
        }
    }

    public void RecordApiError(string error)
    {
        LastApiError = error;
        if (IsApiHealthy)
        {
            IsApiHealthy = false;
            _logger.LogWarning("API health degraded: {Error}", error);
            OnStatusChanged?.Invoke();
        }
    }

    public ValueTask DisposeAsync()
    {
        try
        {
            _dotNetRef?.Dispose();
        }
        catch
        {
            // Ignore disposal errors
        }
        return ValueTask.CompletedTask;
    }
}
