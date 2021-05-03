using System.Threading;
using System.Threading.Tasks;
using Discord.WebSocket;

namespace TrillBot.Discord.Modules.AntiAbuse
{
    internal sealed class DiscordAntiAbuseModule : IDiscordModule
    {
        public const string MessagingTag = "Anti-Abuse";

        private readonly BotImpersonationMonitoring _botImpersonationMonitoring;
        private readonly DiscordSocketClient _client;
        private readonly DiscordGuildUserAvailability _guildUserAvailability;
        private readonly JoinMonitoring _joinMonitoring;

        public DiscordAntiAbuseModule(
            DiscordSocketClient client,
            DiscordGuildUserAvailability guildUserAvailability,
            BotImpersonationMonitoring botImpersonationMonitoring,
            JoinMonitoring joinMonitoring)
        {
            _client = client;
            _guildUserAvailability = guildUserAvailability;
            _botImpersonationMonitoring = botImpersonationMonitoring;
            _joinMonitoring = joinMonitoring;
        }

        public Task InitializeAsync(CancellationToken cancellationToken = default)
        {
            _client.Ready += async () =>
            {
                // We need to use the Ready event for this because we need all users to be available
                // and fetching users somehow doesn't work well with the GuildAvailable events.
                foreach (var guild in _client.Guilds)
                    await OnGuildAvailable(guild);
            };
            _client.JoinedGuild += OnGuildAvailable;
            _client.UserJoined += async user =>
            {
                if (await _joinMonitoring.AddUserAsync(user, cancellationToken)) return;
                if (await _botImpersonationMonitoring.AddUserAsync(user, cancellationToken)) return;
            };
            _client.UserLeft += user =>
            {
                _joinMonitoring.RemoveUser(user);

                return Task.CompletedTask;
            };
            _client.GuildMemberUpdated += async (oldUser, newUser) =>
            {
                if (oldUser.Username == newUser.Username &&
                    oldUser.Nickname == newUser.Nickname)
                    return;

                await _botImpersonationMonitoring.AddUserAsync(newUser, cancellationToken);
            };

            async Task OnGuildAvailable(SocketGuild guild)
            {
                await _guildUserAvailability.EnsureAllUsersAvailableAsync(guild);
                foreach (var user in guild.Users)
                    await _botImpersonationMonitoring.AddUserAsync(user, cancellationToken);
            }

            return Task.CompletedTask;
        }
    }
}