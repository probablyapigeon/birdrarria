using System;
using Terraria.ModLoader;

namespace LonkBirds.Bridge;

/// <summary>
/// Compile-safe contract for the localhost Lonk portal bridge.
/// Networking is intentionally kept behind this contract until tModLoader is
/// available locally; Terraria remains responsible for world mutations.
/// </summary>
public sealed class LonkBridgeProtocol : ModSystem
{
    public const int Version = 1;
    public const int DefaultPort = 45871;
    public const string LoopbackHost = "127.0.0.1";

    public static readonly string[] Kinds = { "hello", "observe", "visit", "teach", "project" };
    public static readonly string[] Birds = { "lonk", "pip" };
    public static readonly string[] Worlds = { "desktop", "terraria" };

    public override void OnWorldLoad()
    {
        // The runtime adapter will connect only after an explicit bridge
        // handshake. Keeping this hook empty makes the mod safe offline.
    }
}
