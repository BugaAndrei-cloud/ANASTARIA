using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace Anastaria.Launcher;

public partial class MainWindow : Window
{
    private readonly LauncherSettings _settings;
    private readonly AnastariaApiClient _api;
    private readonly PatchService _patchService = new();
    private readonly CancellationTokenSource _lifetime = new();
    private readonly LocalizationService _text = new();
    private GameSettingsService? _gameSettings;
    private ComboBox? _resolutionBox, _qualityBox, _fpsBox, _renderScaleBox, _shadowBox;
    private CheckBox? _fullscreenBox, _vsyncBox, _msaaBox, _grassBox, _lightsBox, _trailsBox, _texturesBox, _integratedGpuBox, _musicBox, _effectsBox;
    private Slider? _musicVolume, _effectsVolume;

    public MainWindow()
    {
        InitializeComponent();
        _settings = LauncherSettings.Load();
        _api = new AnastariaApiClient(_settings.ApiBaseUrl);
        LanguageBox.ItemsSource = LocalizationService.Languages;
        LanguageBox.DisplayMemberPath = "Value";
        LanguageBox.SelectedValuePath = "Key";
        LanguageBox.SelectedValue = _text.CurrentCode;
        ApplyLanguage();
        Loaded += async (_, _) => await RefreshStatusAsync();
        Closed += (_, _) => { _lifetime.Cancel(); _api.Dispose(); _patchService.Dispose(); };
    }

    private void LanguageBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (LanguageBox.SelectedValue is not string code) return;
        _text.SetLanguage(code);
        ApplyLanguage();
        Home_Click(this, new RoutedEventArgs());
        _ = RefreshStatusAsync();
    }

    private void ApplyLanguage()
    {
        HomeButton.Content = _text["home"];
        NewsButton.Content = _text["news"];
        EventsButton.Content = _text["events"];
        ShopButton.Content = _text["shop"];
        SettingsButton.Content = _text["settings"];
        WebsiteButton.Content = _text["website"];
        LoginButton.Content = _text["login"];
        RepairButton.Content = _text["repair"];
        PlayButton.Content = _text["play"];
        UsernameBox.ToolTip = _text["username"];
        PasswordBox.ToolTip = _text["password"];
        PageTitle.Text = _text["welcome"];
        PageSubtitle.Text = _text["official"];
        HeroTitle.Text = _text["hero"];
        HeroDetail.Text = _text["heroDetail"];
        OperationLabel.Text = _text["ready"];
        ServerLabel.Text = _text["checking"];
    }

    private async Task RefreshStatusAsync()
    {
        try
        {
            ServerStatus? status = await _api.GetStatusAsync(_lifetime.Token);
            ServerLabel.Text = status?.Status == "online" ? string.Format(_text["online"], status.PlayersOnline ?? 0) : _text["offline"];
            ServerLabel.Foreground = status?.Status == "online" ? Brushes.LightGreen : Brushes.IndianRed;
        }
        catch
        {
            ServerLabel.Text = _text["apiUnavailable"];
            ServerLabel.Foreground = Brushes.IndianRed;
        }
    }

    private void Home_Click(object sender, RoutedEventArgs e)
    {
        SetPage(_text["welcome"], _text["official"]);
        AddText(_text["hero"], 34, true);
        AddText(_text["heroDetail"], 16);
    }

    private async void News_Click(object sender, RoutedEventArgs e)
    {
        SetPage(_text["news"], _text["newsSubtitle"]);
        await LoadAsync(async () =>
        {
            NewsResponse? response = await _api.GetNewsAsync(_lifetime.Token);
            foreach (NewsArticle item in response?.Items ?? []) AddCard(item.Title, item.Summary ?? item.Category);
        });
    }

    private async void Events_Click(object sender, RoutedEventArgs e)
    {
        SetPage(_text["events"], _text["eventsSubtitle"]);
        await LoadAsync(async () =>
        {
            EventsResponse? response = await _api.GetEventsAsync(_lifetime.Token);
            foreach (GameEvent item in response?.Items ?? []) AddCard(item.Slug.Replace('-', ' '), $"{item.Schedule} • {item.Timezone}");
        });
    }

    private async void Shop_Click(object sender, RoutedEventArgs e)
    {
        SetPage(_text["shop"], _text["shopSubtitle"]);
        await LoadAsync(async () =>
        {
            CommerceCatalog? response = await _api.GetShopAsync(_lifetime.Token);
            foreach (ShopProduct item in response?.Products ?? []) AddCard(item.Title, $"{item.PriceAmount} {item.CurrencyCode}");
        });
    }

    private void Settings_Click(object sender, RoutedEventArgs e)
    {
        SetPage("SETĂRI", "Configurarea instalării");
        _gameSettings = new GameSettingsService(ResolveGamePath());
        GameSettings value = _gameSettings.Load();
        AddSection("DISPLAY");
        _resolutionBox = AddChoice("Rezoluție", ["1280x720", "1366x768", "1600x900", "1920x1080", "2560x1440", "3840x2160"], $"{value.Width}x{value.Height}");
        _fullscreenBox = AddCheck("Fullscreen", value.Fullscreen);
        _vsyncBox = AddCheck("V-Sync", value.VSync);
        _fpsBox = AddChoice("Limită FPS", ["60", "Nelimitat"], value.FrameRateLimit <= 0 ? "Nelimitat" : "60");
        AddSection("GRAFICĂ ȘI PERFORMANȚĂ");
        _qualityBox = AddChoice("Preset", ["Auto", "Low", "Medium", "High"], value.QualityPreset);
        _renderScaleBox = AddChoice("Render scale", ["Auto", "50%", "60%", "75%", "100%", "125%", "150%", "200%", "300%"], value.RenderScale is null ? "Auto" : $"{value.RenderScale * 100:0}%");
        _shadowBox = AddChoice("Umbre", ["Off", "Low", "Medium", "High", "Ultra"], value.ShadowQuality);
        _msaaBox = AddCheck("Anti-aliasing MSAA", value.Msaa ?? false);
        _grassBox = AddCheck("Iarbă", value.Grass); _lightsBox = AddCheck("Lumini dinamice", value.DynamicLights);
        _trailsBox = AddCheck("Urme arme", value.WeaponTrails); _texturesBox = AddCheck("Texturi de calitate", value.HighQualityTextures);
        _integratedGpuBox = AddCheck("Optimizare GPU integrat", value.OptimizeForIntegratedGpu);
        AddSection("AUDIO");
        _musicBox = AddCheck("Muzică", value.MusicEnabled); _musicVolume = AddSlider("Volum muzică", value.MusicVolume);
        _effectsBox = AddCheck("Efecte sonore", value.EffectsEnabled); _effectsVolume = AddSlider("Volum efecte", value.EffectsVolume);
        var save = new Button { Content = "SALVEAZĂ SETĂRILE", Background = new SolidColorBrush(Color.FromRgb(165, 122, 44)), HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 20, 0, 5) };
        save.Click += SaveSettings_Click; ContentPanel.Children.Add(save);
    }

    private void SaveSettings_Click(object sender, RoutedEventArgs e)
    {
        if (_gameSettings is null || _resolutionBox is null) return;
        string[] size = (_resolutionBox.SelectedItem?.ToString() ?? "1280x720").Split('x');
        double? renderScale = (_renderScaleBox?.SelectedItem?.ToString()) switch
        {
            "50%" => .5, "60%" => .6, "75%" => .75, "100%" => 1, "125%" => 1.25,
            "150%" => 1.5, "200%" => 2, "300%" => 3, _ => null,
        };
        var value = new GameSettings(int.Parse(size[0]), int.Parse(size[1]), _fullscreenBox?.IsChecked == true,
            _qualityBox?.SelectedItem?.ToString() ?? "Auto", _vsyncBox?.IsChecked == true,
            _fpsBox?.SelectedItem?.ToString() == "Nelimitat" ? 0 : 60, renderScale, _msaaBox?.IsChecked,
            _shadowBox?.SelectedItem?.ToString() ?? "Off", _grassBox?.IsChecked == true, _lightsBox?.IsChecked == true,
            _trailsBox?.IsChecked == true, _texturesBox?.IsChecked == true, _integratedGpuBox?.IsChecked == true,
            _musicBox?.IsChecked == true, (int)(_musicVolume?.Value ?? 50), _effectsBox?.IsChecked == true, (int)(_effectsVolume?.Value ?? 100));
        _gameSettings.Save(value); OperationLabel.Text = "Setările jocului au fost salvate.";
    }

    private async void Login_Click(object sender, RoutedEventArgs e)
    {
        LoginButton.IsEnabled = false;
        try
        {
            await _api.LoginAsync(UsernameBox.Text.Trim(), PasswordBox.Password, _lifetime.Token);
            PasswordBox.Clear();
            LoginButton.Content = "CONECTAT";
            OperationLabel.Text = $"Autentificat ca {UsernameBox.Text.Trim()}";
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            MessageBox.Show(ex.Message, "ANASTARIA Login", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        finally
        {
            LoginButton.IsEnabled = true;
        }
    }

    private async void Repair_Click(object sender, RoutedEventArgs e)
    {
        if (_settings.PatchManifestUrl is null)
        {
            MessageBox.Show("Manifestul de patch trebuie publicat și configurat înainte de reparare.", "ANASTARIA");
            return;
        }

        RepairButton.IsEnabled = false;
        PlayButton.IsEnabled = false;
        try
        {
            OperationLabel.Text = "Verific fișierele...";
            var progress = new Progress<PatchProgress>(UpdatePatchProgress);
            string version = await _patchService.VerifyAndRepairAsync(_settings.PatchManifestUrl, Path.GetDirectoryName(ResolveGamePath())!,
                _settings.PatchPublicKeyPem, progress, _lifetime.Token);
            PatchProgress.Value = 100;
            OperationLabel.Text = $"Client actualizat • versiunea {version}";
        }
        catch (OperationCanceledException) { OperationLabel.Text = "Actualizare anulată."; }
        catch (Exception ex)
        {
            OperationLabel.Text = "Actualizarea a eșuat.";
            MessageBox.Show(ex.Message, "ANASTARIA Patcher", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally { RepairButton.IsEnabled = true; PlayButton.IsEnabled = File.Exists(ResolveGamePath()); }
    }

    private void UpdatePatchProgress(PatchProgress value)
    {
        PatchProgress.Value = value.Fraction * 100;
        string speed = value.BytesPerSecond > 0 ? $" • {FormatBytes(value.BytesPerSecond)}/s" : string.Empty;
        OperationLabel.Text = $"{value.CompletedFiles}/{value.TotalFiles} • {value.FileName} • {value.Fraction:P0}{speed}";
    }

    private static string FormatBytes(double bytes) => bytes switch
    {
        >= 1024 * 1024 * 1024 => $"{bytes / (1024 * 1024 * 1024):0.0} GB",
        >= 1024 * 1024 => $"{bytes / (1024 * 1024):0.0} MB",
        >= 1024 => $"{bytes / 1024:0.0} KB",
        _ => $"{bytes:0} B",
    };

    private void Play_Click(object sender, RoutedEventArgs e)
    {
        string executable = ResolveGamePath();
        if (!File.Exists(executable))
        {
            MessageBox.Show($"Clientul nu a fost găsit:\n{executable}", "ANASTARIA", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        Process.Start(new ProcessStartInfo(executable) { WorkingDirectory = Path.GetDirectoryName(executable)!, UseShellExecute = true });
        Close();
    }

    private void Website_Click(object sender, RoutedEventArgs e) =>
        Process.Start(new ProcessStartInfo(_settings.WebsiteUrl.ToString()) { UseShellExecute = true });

    private string ResolveGamePath() => Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, _settings.GameExecutablePath));

    private async Task LoadAsync(Func<Task> action)
    {
        try { await action(); }
        catch (Exception ex) { AddText($"Datele nu sunt disponibile: {ex.Message}", 15); }
    }

    private void SetPage(string title, string subtitle)
    {
        PageTitle.Text = title;
        PageSubtitle.Text = subtitle;
        ContentPanel.Children.Clear();
    }

    private void AddCard(string title, string detail)
    {
        var panel = new StackPanel { Margin = new Thickness(0, 0, 0, 12) };
        panel.Children.Add(new TextBlock { Text = title, FontSize = 18, FontWeight = FontWeights.SemiBold, TextWrapping = TextWrapping.Wrap });
        panel.Children.Add(new TextBlock { Text = detail, Foreground = Brushes.LightSlateGray, Margin = new Thickness(0, 5, 0, 0), TextWrapping = TextWrapping.Wrap });
        ContentPanel.Children.Add(new Border { Background = new SolidColorBrush(Color.FromRgb(23, 32, 51)), CornerRadius = new CornerRadius(6), Padding = new Thickness(16), Child = panel });
    }

    private void AddSection(string title) => ContentPanel.Children.Add(new TextBlock
    {
        Text = title, Foreground = new SolidColorBrush(Color.FromRgb(215, 165, 60)), FontSize = 12,
        FontWeight = FontWeights.Bold, Margin = new Thickness(0, 16, 0, 8),
    });

    private ComboBox AddChoice(string label, string[] values, string selected)
    {
        var row = CreateSettingRow(label); var box = new ComboBox { Width = 220, ItemsSource = values, SelectedItem = values.Contains(selected) ? selected : values[0] };
        Grid.SetColumn(box, 1); row.Children.Add(box); ContentPanel.Children.Add(row); return box;
    }

    private CheckBox AddCheck(string label, bool selected)
    {
        var row = CreateSettingRow(label); var box = new CheckBox { IsChecked = selected, VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right };
        Grid.SetColumn(box, 1); row.Children.Add(box); ContentPanel.Children.Add(row); return box;
    }

    private Slider AddSlider(string label, int value)
    {
        var row = CreateSettingRow(label); var slider = new Slider { Minimum = 0, Maximum = 100, Value = value, Width = 220, TickFrequency = 10, IsSnapToTickEnabled = true };
        Grid.SetColumn(slider, 1); row.Children.Add(slider); ContentPanel.Children.Add(row); return slider;
    }

    private static Grid CreateSettingRow(string label)
    {
        var row = new Grid { Margin = new Thickness(0, 5, 0, 5), MaxWidth = 620, HorizontalAlignment = HorizontalAlignment.Left };
        row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(300) }); row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(240) });
        row.Children.Add(new TextBlock { Text = label, Foreground = Brushes.LightGray, VerticalAlignment = VerticalAlignment.Center }); return row;
    }

    private void AddText(string text, double size, bool bold = false) => ContentPanel.Children.Add(new TextBlock
    {
        Text = text, FontSize = size, FontWeight = bold ? FontWeights.Bold : FontWeights.Normal,
        Foreground = bold ? Brushes.White : Brushes.LightSlateGray, Margin = new Thickness(0, 10, 0, 5), TextWrapping = TextWrapping.Wrap,
    });
}
