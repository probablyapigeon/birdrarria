using Terraria.ModLoader;

namespace LonkBirds;

public sealed class LonkBirds : Mod
{
    internal const byte SummonLonkMessage = 1;

    public override void HandlePacket(System.IO.BinaryReader reader, int whoAmI)
    {
        byte message = reader.ReadByte();
        if (message != SummonLonkMessage)
            return;

        // The first slice is single-player friendly. Multiplayer validation and
        // XC bridge messages will be added before networked companion state.
    }
}