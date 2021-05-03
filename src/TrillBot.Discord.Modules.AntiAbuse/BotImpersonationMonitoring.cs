using System.Threading;
using System.Threading.Tasks;
using Discord;
using Discord.WebSocket;
using Microsoft.Extensions.Localization;
using TrillBot.Discord.Modules.AntiAbuse.Confusables;

namespace TrillBot.Discord.Modules.AntiAbuse
{
    public class BotImpersonationMonitoring
    {
        private readonly DiscordSocketClient _client;
        private readonly ConfusablesDetection _confusablesDetection;
        private readonly IStringLocalizer<BotImpersonationMonitoring> _localizer;
        private readonly DiscordMessaging _messaging;

        public BotImpersonationMonitoring(
            DiscordSocketClient client,
            DiscordMessaging messaging,
            IStringLocalizer<BotImpersonationMonitoring> localizer)
        {
            _client = client;
            _messaging = messaging;
            _localizer = localizer;
            _confusablesDetection = new ConfusablesDetection(new ConfusablesCache());
        }

        public async Task<bool> AddUserAsync(IGuildUser user, CancellationToken cancellationToken = default)
        {
            var bot = await user.Guild.GetUserAsync(_client.CurrentUser.Id);
            if (user.Id == bot.Id)
                return false;
            if (user.Id == 177726019959128065)
                // Original account of TrilluXe himself.
                return false;

            var names = new[]
            {
                bot.Nickname ?? bot.Username,
                "TrilluXe"
            };
            var userName = user.Nickname ?? user.Username;

            string confusableName = null;
            foreach (var name in names)
                if (await _confusablesDetection.TestConfusabilityAsync(name, userName, cancellationToken))
                {
                    confusableName = name;
                    break;
                }

            if (confusableName == null)
                return false;

            // TODO: Re-enable DMs for kicks.
            //var notified = await DiscordMessaging.LogUserAsync(
            //    user,
            //    _localizer["YouWereKicked", bot.Guild.Name, userName],
            //    cancellationToken: cancellationToken);
            await _messaging.LogGuildAsync(
                bot.Guild,
                DiscordAntiAbuseModule.MessagingTag,
                $"{_localizer["UserWasKicked", user.Mention, userName, bot.Mention]}"/*\n" +
                $"*{(notified ? _localizer["UserWasNotified"] : _localizer["UserWasNotNotified"])}*"*/,
                cancellationToken: cancellationToken);

            // Kick afterwards, or messaging the user will not work anymore.
            await user.KickAsync(
                $"[{DiscordAntiAbuseModule.MessagingTag}] {_localizer["UserKickReason", userName, confusableName]}");
            return true;
        }
    }
}