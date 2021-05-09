using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Discord;
using Microsoft.Extensions.Localization;
using TrillBot.Discord.Modules.AntiAbuse.Confusables;

namespace TrillBot.Discord.Modules.AntiAbuse
{
    internal sealed class JoinMonitoring
    {
        private readonly ConfusablesDetection _confusablesDetection;
        private readonly IStringLocalizer<JoinMonitoring> _localizer;
        private readonly DiscordMessaging _messaging;

        private readonly IDictionary<IGuild, RecentlyJoinedUsers> _recentlyJoinedUsers =
            new Dictionary<IGuild, RecentlyJoinedUsers>();

        public JoinMonitoring(
            ConfusablesDetection confusablesDetection,
            IStringLocalizer<JoinMonitoring> localizer,
            DiscordMessaging messaging)
        {
            _confusablesDetection = confusablesDetection;
            _localizer = localizer;
            _messaging = messaging;
        }

        public async Task<bool> AddUserAsync(IGuildUser user, CancellationToken cancellationToken = default)
        {
            var recentlyJoinedUsers = GetOrCreateRecentlyJoinedUsers(user.Guild);

            await recentlyJoinedUsers.AddAsync(user, cancellationToken);
            await recentlyJoinedUsers.EnsureUserCountWarningAsync(cancellationToken);
            return await recentlyJoinedUsers.EnsureConfusableUsersBannedAsync(cancellationToken);
        }

        public void RemoveUser(IGuildUser user)
        {
            var recentlyJoinedUsers = GetOrCreateRecentlyJoinedUsers(user.Guild);

            recentlyJoinedUsers.Remove(user);
        }

        private RecentlyJoinedUsers GetOrCreateRecentlyJoinedUsers(IGuild guild)
        {
            if (!_recentlyJoinedUsers.ContainsKey(guild))
                _recentlyJoinedUsers[guild] = new RecentlyJoinedUsers(this, guild);
            return _recentlyJoinedUsers[guild];
        }

        private sealed class JoinedUser
        {
            private readonly JoinMonitoring _joinMonitoring;

            public JoinedUser(JoinMonitoring joinMonitoring, IGuildUser user)
            {
                _joinMonitoring = joinMonitoring;
                User = user;
            }

            public IGuildUser User { get; }
            public DateTime Joined { get; } = DateTime.UtcNow;
            public bool Available { get; private set; } = true;

            public async Task BanAsync(CancellationToken cancellationToken = default)
            {
                if (!Available) return;

                await User.BanAsync(
                    reason: $"[{DiscordAntiAbuseModule.MessagingTag}] {_joinMonitoring._localizer["UserBanReason"]}");

                Remove();
            }

            public void Remove()
            {
                Available = false;
            }
        }

        private sealed class RecentlyJoinedUsers
        {
            private readonly ICollection<JoinedUser> _all =
                new List<JoinedUser>();

            private readonly ISet<string> _bannedConfusableUserNames = new HashSet<string>();

            private readonly IDictionary<string, ICollection<JoinedUser>> _byName =
                new Dictionary<string, ICollection<JoinedUser>>();

            private readonly IGuild _guild;

            private readonly JoinMonitoring _joinMonitoring;

            private bool _userCountWarningIssued;

            public RecentlyJoinedUsers(JoinMonitoring joinMonitoring, IGuild guild)
            {
                _joinMonitoring = joinMonitoring;
                _guild = guild;
            }

            public async Task AddAsync(IGuildUser user, CancellationToken cancellationToken = default)
            {
                if (_all.Any(_ => _.User.Id == user.Id))
                    return;

                var newUser = new JoinedUser(_joinMonitoring, user);
                var newUserName = user.Nickname ?? user.Username;

                _all.Add(newUser);

                var added = false;

                foreach (var (userName, users) in _byName)
                    if (await _joinMonitoring._confusablesDetection.TestConfusabilityAsync(
                        userName,
                        newUserName,
                        cancellationToken))
                    {
                        users.Add(newUser);
                        added = true;
                    }

                if (!added)
                    _byName[newUserName] = new List<JoinedUser> {newUser};
            }

            public void Remove(IGuildUser user)
            {
                foreach (var existingUser in _all)
                    if (existingUser.User.Id == user.Id)
                        existingUser.Remove();
            }

            public async Task EnsureUserCountWarningAsync(CancellationToken cancellationToken = default)
            {
                if (!IsUserCountWarningRequired())
                    return;

                /*await _guild.ModifyAsync(
                    _ => _.VerificationLevel = Optional.Create(VerificationLevel.Extreme),
                    new RequestOptions
                    {
                        CancelToken = cancellationToken
                    });*/
                await _joinMonitoring._messaging.LogGuildAsync(
                    _guild,
                    DiscordAntiAbuseModule.MessagingTag,
                    $"{_joinMonitoring._localizer["Warning"]}",
                    cancellationToken: cancellationToken);
            }

            public async Task<bool> EnsureConfusableUsersBannedAsync(CancellationToken cancellationToken = default)
            {
                var anyoneBanned = false;

                foreach (var (confusableUserName, confusableUsers) in GetUnbannedConfusableUsers())
                {
                    if (!_bannedConfusableUserNames.Contains(confusableUserName))
                    {
                        await _joinMonitoring._messaging.LogGuildAsync(
                            _guild,
                            DiscordAntiAbuseModule.MessagingTag,
                            $"{_joinMonitoring._localizer["UserWasBanned", confusableUserName]}",
                            cancellationToken: cancellationToken);
                        _bannedConfusableUserNames.Add(confusableUserName);
                    }

                    foreach (var confusableUser in confusableUsers)
                    {
                        await confusableUser.BanAsync(cancellationToken);
                        anyoneBanned = true;
                    }
                }

                return anyoneBanned;
            }

            private bool IsUserCountWarningRequired()
            {
                RemoveOld();

                var now = DateTime.UtcNow;
                var count = _all.Count(_ => now - _.Joined <= UserCountWarningConfiguration.Timeframe);

                if (count >= UserCountWarningConfiguration.OnThreshold && !_userCountWarningIssued)
                {
                    _userCountWarningIssued = true;
                    return true;
                }

                if (count <= UserCountWarningConfiguration.OffThreshold) _userCountWarningIssued = false;

                return false;
            }

            private IDictionary<string, IEnumerable<JoinedUser>> GetUnbannedConfusableUsers()
            {
                RemoveOld();

                var now = DateTime.UtcNow;

                return _byName
                    .Where(_1 =>
                        _1.Value.Count(_2 => now - _2.Joined <= ConfusableUserCountConfiguration.Timeframe) >=
                        ConfusableUserCountConfiguration.Threshold)
                    .ToDictionary(
                        _ => _.Key,
                        _1 => _1.Value.Where(_2 => _2.Available));
            }

            private void RemoveOld()
            {
                var trackingTimeframe =
                    UserCountWarningConfiguration.Timeframe > ConfusableUserCountConfiguration.Timeframe
                        ? UserCountWarningConfiguration.Timeframe
                        : ConfusableUserCountConfiguration.Timeframe;
                var now = DateTime.UtcNow;

                foreach (var (userName, users) in _byName)
                {
                    foreach (var user in users)
                        if (now - user.Joined > trackingTimeframe)
                        {
                            _all.Remove(user);
                            users.Remove(user);
                        }

                    if (users.Count == 0)
                        _byName.Remove(userName);
                }
            }

            // If more than 15 users join within one hour, issue a warning.
            // Issue a new warning only if this happens again after join rate has dropped below 10 users per hour.
            private static class UserCountWarningConfiguration
            {
                public const int OnThreshold = 15 + 1;
                public const int OffThreshold = 10 - 1;
                public static readonly TimeSpan Timeframe = TimeSpan.FromHours(1);
            }

            // If more than 3 user with confusable names join within one day, ban all of them automatically.
            private static class ConfusableUserCountConfiguration
            {
                public const int Threshold = 5;
                public static readonly TimeSpan Timeframe = TimeSpan.FromDays(1);
            }
        }
    }
}