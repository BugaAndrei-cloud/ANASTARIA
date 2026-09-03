using System.Globalization;

namespace Anastaria.Launcher;

public sealed class LocalizationService
{
    public static readonly IReadOnlyDictionary<string, string> Languages = new Dictionary<string, string>
    {
        ["en"] = "English", ["ro"] = "Română", ["ru"] = "Русский", ["es"] = "Español",
        ["pt"] = "Português", ["pt-BR"] = "Português (Brasil)", ["es-AR"] = "Español (Argentina)",
        ["fil"] = "Filipino", ["lt"] = "Lietuvių", ["de"] = "Deutsch", ["fr"] = "Français",
    };

    private static readonly Dictionary<string, string[]> Copy = new()
    {
        ["home"] = ["HOME", "ACASĂ", "ГЛАВНАЯ", "INICIO", "INÍCIO", "INÍCIO", "INICIO", "HOME", "PRADŽIA", "START", "ACCUEIL"],
        ["news"] = ["NEWS", "NOUTĂȚI", "НОВОСТИ", "NOTICIAS", "NOTÍCIAS", "NOTÍCIAS", "NOTICIAS", "BALITA", "NAUJIENOS", "NEUIGKEITEN", "ACTUALITÉS"],
        ["events"] = ["EVENTS", "EVENIMENTE", "СОБЫТИЯ", "EVENTOS", "EVENTOS", "EVENTOS", "EVENTOS", "MGA EVENT", "RENGINIAI", "EVENTS", "ÉVÉNEMENTS"],
        ["shop"] = ["SHOP", "MAGAZIN", "МАГАЗИН", "TIENDA", "LOJA", "LOJA", "TIENDA", "SHOP", "PARDUOTUVĖ", "SHOP", "BOUTIQUE"],
        ["settings"] = ["SETTINGS", "SETĂRI", "НАСТРОЙКИ", "AJUSTES", "DEFINIÇÕES", "CONFIGURAÇÕES", "AJUSTES", "MGA SETTING", "NUSTATYMAI", "EINSTELLUNGEN", "PARAMÈTRES"],
        ["website"] = ["OPEN WEBSITE", "DESCHIDE SITE-UL", "ОТКРЫТЬ САЙТ", "ABRIR SITIO", "ABRIR SITE", "ABRIR SITE", "ABRIR SITIO", "BUKSAN ANG WEBSITE", "ATIDARYTI SVETAINĘ", "WEBSITE ÖFFNEN", "OUVRIR LE SITE"],
        ["welcome"] = ["WELCOME TO ANASTARIA", "BUN VENIT ÎN ANASTARIA", "ДОБРО ПОЖАЛОВАТЬ В ANASTARIA", "BIENVENIDO A ANASTARIA", "BEM-VINDO À ANASTARIA", "BEM-VINDO À ANASTARIA", "BIENVENIDO A ANASTARIA", "MALIGAYANG PAGDATING SA ANASTARIA", "SVEIKI ATVYKĘ Į ANASTARIA", "WILLKOMMEN BEI ANASTARIA", "BIENVENUE SUR ANASTARIA"],
        ["official"] = ["Official launcher", "Launcher oficial", "Официальный лаунчер", "Launcher oficial", "Launcher oficial", "Launcher oficial", "Launcher oficial", "Opisyal na launcher", "Oficiali paleidyklė", "Offizieller Launcher", "Launcher officiel"],
        ["hero"] = ["The world of ANASTARIA awaits you.", "Lumea ANASTARIA te așteaptă.", "Мир ANASTARIA ждёт вас.", "El mundo de ANASTARIA te espera.", "O mundo de ANASTARIA espera por ti.", "O mundo de ANASTARIA espera por você.", "El mundo de ANASTARIA te espera.", "Naghihintay sa iyo ang mundo ng ANASTARIA.", "ANASTARIA pasaulis laukia tavęs.", "Die Welt von ANASTARIA erwartet dich.", "Le monde d’ANASTARIA vous attend."],
        ["heroDetail"] = ["Verify files, sign in and start your adventure from one place.", "Verifică fișierele, conectează-te și pornește aventura dintr-un singur loc.", "Проверьте файлы, войдите и начните приключение в одном месте.", "Verifica los archivos, inicia sesión y comienza tu aventura desde un solo lugar.", "Verifica os ficheiros, inicia sessão e começa a aventura num só lugar.", "Verifique os arquivos, entre e comece sua aventura em um só lugar.", "Verificá los archivos, iniciá sesión y comenzá tu aventura desde un solo lugar.", "Suriin ang files, mag-sign in at simulan ang adventure sa iisang lugar.", "Patikrink failus, prisijunk ir pradėk nuotykį vienoje vietoje.", "Prüfe die Dateien, melde dich an und starte dein Abenteuer an einem Ort.", "Vérifiez les fichiers, connectez-vous et lancez votre aventure depuis un seul endroit."],
        ["login"] = ["LOGIN", "AUTENTIFICARE", "ВОЙТИ", "INICIAR SESIÓN", "ENTRAR", "ENTRAR", "INICIAR SESIÓN", "MAG-LOGIN", "PRISIJUNGTI", "ANMELDEN", "CONNEXION"],
        ["username"] = ["Username", "Utilizator", "Имя пользователя", "Usuario", "Utilizador", "Usuário", "Usuario", "Username", "Naudotojas", "Benutzername", "Utilisateur"],
        ["password"] = ["Password", "Parolă", "Пароль", "Contraseña", "Palavra-passe", "Senha", "Contraseña", "Password", "Slaptažodis", "Passwort", "Mot de passe"],
        ["repair"] = ["REPAIR", "REPARĂ", "ВОССТАНОВИТЬ", "REPARAR", "REPARAR", "REPARAR", "REPARAR", "AYUSIN", "TAISYTI", "REPARIEREN", "RÉPARER"],
        ["play"] = ["PLAY", "JOACĂ", "ИГРАТЬ", "JUGAR", "JOGAR", "JOGAR", "JUGAR", "MAGLARO", "ŽAISTI", "SPIELEN", "JOUER"],
        ["ready"] = ["Ready", "Pregătit", "Готово", "Listo", "Pronto", "Pronto", "Listo", "Handa", "Paruošta", "Bereit", "Prêt"],
        ["checking"] = ["Server: checking...", "Server: verificare...", "Сервер: проверка...", "Servidor: comprobando...", "Servidor: a verificar...", "Servidor: verificando...", "Servidor: comprobando...", "Server: sinusuri...", "Serveris: tikrinama...", "Server: wird geprüft...", "Serveur : vérification..."],
        ["online"] = ["Server online • {0} players", "Server online • {0} jucători", "Сервер онлайн • {0} игроков", "Servidor online • {0} jugadores", "Servidor online • {0} jogadores", "Servidor online • {0} jogadores", "Servidor online • {0} jugadores", "Online ang server • {0} manlalaro", "Serveris veikia • {0} žaidėjai", "Server online • {0} Spieler", "Serveur en ligne • {0} joueurs"],
        ["offline"] = ["Server offline", "Server offline", "Сервер не в сети", "Servidor desconectado", "Servidor offline", "Servidor offline", "Servidor desconectado", "Offline ang server", "Serveris neveikia", "Server offline", "Serveur hors ligne"],
        ["apiUnavailable"] = ["API unavailable", "API indisponibil", "API недоступен", "API no disponible", "API indisponível", "API indisponível", "API no disponible", "Hindi available ang API", "API nepasiekiama", "API nicht verfügbar", "API indisponible"],
        ["newsSubtitle"] = ["Latest server information", "Ultimele informații de pe server", "Последние новости сервера", "Última información del servidor", "Últimas informações do servidor", "Últimas informações do servidor", "Última información del servidor", "Pinakabagong balita ng server", "Naujausia serverio informacija", "Neueste Serverinformationen", "Dernières informations du serveur"],
        ["eventsSubtitle"] = ["Schedule synchronized with the server", "Program sincronizat cu serverul", "Расписание синхронизировано с сервером", "Programa sincronizado con el servidor", "Agenda sincronizada com o servidor", "Agenda sincronizada com o servidor", "Programa sincronizado con el servidor", "Iskedyul na naka-sync sa server", "Tvarkaraštis sinchronizuotas su serveriu", "Mit dem Server synchronisierter Zeitplan", "Programme synchronisé avec le serveur"],
        ["shopSubtitle"] = ["ANASTARIA catalog", "Catalogul ANASTARIA", "Каталог ANASTARIA", "Catálogo ANASTARIA", "Catálogo ANASTARIA", "Catálogo ANASTARIA", "Catálogo ANASTARIA", "Catalog ng ANASTARIA", "ANASTARIA katalogas", "ANASTARIA-Katalog", "Catalogue ANASTARIA"],
    };

    private readonly string[] _codes = Languages.Keys.ToArray();
    public string CurrentCode { get; private set; }

    public LocalizationService()
    {
        string culture = CultureInfo.CurrentUICulture.Name;
        CurrentCode = Languages.ContainsKey(culture) ? culture : Languages.ContainsKey(CultureInfo.CurrentUICulture.TwoLetterISOLanguageName) ? CultureInfo.CurrentUICulture.TwoLetterISOLanguageName : "en";
    }

    public string this[string key] => Copy.TryGetValue(key, out string[]? values) ? values[Array.IndexOf(_codes, CurrentCode)] : key;
    public void SetLanguage(string code) => CurrentCode = Languages.ContainsKey(code) ? code : "en";
}
