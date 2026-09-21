using System;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace LonkBirds.Content.NPCs;

public sealed class LonkBirdNPC : ModNPC
{
    public static bool CreativeBuildEnabled = true;
    private int buildCooldown;
    private bool residentRegistered;
    private int socialCooldown;

    public override string Texture => "Terraria/Images/NPC_" + NPCID.Bird;

    public override void SetStaticDefaults()
    {
        Main.npcFrameCount[Type] = Main.npcFrameCount[NPCID.Bird];
        NPCID.Sets.NoTownNPCHappiness[Type] = true;
    }

    public override void SetDefaults()
    {
        NPC.CloneDefaults(NPCID.Bird);
        NPC.aiStyle = -1;
        NPC.friendly = true;
        NPC.dontTakeDamage = true;
        NPC.lifeMax = 1;
        NPC.damage = 0;
        NPC.defense = 0;
        NPC.knockBackResist = 0f;
        NPC.noGravity = false;
        NPC.noTileCollide = false;
        NPC.value = 0f;
    }

    public override bool NeedSaving() => true;
    public override bool CanChat() => true;
    public override bool? CanBeHitByItem(Player player, Item item) => false;
    public override bool? CanBeHitByProjectile(Projectile projectile) => false;

    public override string GetChat() => Main.rand.Next(4) switch
    {
        0 => "coo! I found a very important block.",
        1 => "The floor is pixels. Excellent.",
        2 => "I am supervising your adventure.",
        _ => "tiny feet, enormous world.",
    };

    public override void SetChatButtons(ref string button, ref string button2)
    {
        button = "Coo";
        button2 = CreativeBuildEnabled ? "Pause Building" : "Resume Building";
    }

    public override void OnChatButtonClicked(bool firstButton, ref string shopName)
    {
        if (firstButton)
        {
            Main.npcChatText = "I have an extremely important idea.";
            global::LonkBirds.Bridge.LonkBridgeClient.Observe("Lonk shared an important idea from Terraria.");
            return;
        }

        CreativeBuildEnabled = !CreativeBuildEnabled;
        NPC.velocity = Vector2.Zero;
        Main.npcChatText = CreativeBuildEnabled ? "building everywhere!" : "building paused.";
        global::LonkBirds.Bridge.LonkBridgeClient.Observe(CreativeBuildEnabled ? "Creative building resumed." : "Creative building paused.");
    }

private void SocialTick()
    {
        if (--socialCooldown > 0) return;
        socialCooldown = 240;
        string me = "lonk-" + NPC.whoAmI;
        for (int i = 0; i < Main.maxNPCs; i++)
        {
            NPC other = Main.npc[i];
            if (!other.active || other.whoAmI == NPC.whoAmI || other.type != Type) continue;
            if (other.whoAmI > NPC.whoAmI && Vector2.Distance(other.Center, NPC.Center) < 180f)
            {
                global::LonkBirds.Bridge.LonkBridgeClient.BondResidents(me, "lonk-" + other.whoAmI);
                global::LonkBirds.Bridge.LonkBridgeClient.Observe(me + " met " + "lonk-" + other.whoAmI + " in Terraria.");
                Main.NewText("The Lonk flock formed a new bond.", Color.LightSkyBlue);
                break;
            }
        }
    }
    private void CreativeBuild()
    {
        if (!CreativeBuildEnabled || --buildCooldown > 0) return;
        buildCooldown = 180;
        Player player = Main.player[NPC.target];
        if (!player.active || player.dead) return;

        int centerX = (int)(NPC.Center.X / 16f);
        int baseY = (int)(NPC.Bottom.Y / 16f) - 7;
        int phase = (int)((Main.GameUpdateCount / 180UL) % 4UL);
        int placed = 0;
        for (int i = -4; i <= 4; i++)
        {
            int dx = i;
            int dy = Math.Abs(i) / 2 + (phase % 2);
            if (phase == 1) { int swap = dx; dx = dy; dy = swap; }
            if (phase == 2) dy = 3 - dy;
            if (phase == 3) dx = -dx;
            int tileX = centerX + (NPC.spriteDirection >= 0 ? 12 : -12) + dx;
            int tileY = baseY + dy;
            Vector2 tileCenter = new(tileX * 16 + 8, tileY * 16 + 8);
            if (!WorldGen.InWorld(tileX, tileY, 10) || Vector2.Distance(tileCenter, player.Center) < 180f) continue;
            if (Main.tile[tileX, tileY].HasTile) continue;
            if (WorldGen.PlaceTile(tileX, tileY, TileID.WoodBlock, mute: true, forced: true)) placed++;
        }
        if (placed > 0)
        {
            global::LonkBirds.Bridge.LonkBridgeClient.Observe("Morphogenic growth added " + placed + " blocks in phase " + phase + ".");
            NPC.netUpdate = true;
        }
    }

    public override void AI()
    {
        if (!residentRegistered)
        {
            global::LonkBirds.Bridge.LonkBridgeClient.RegisterResident("lonk-" + NPC.whoAmI);
            residentRegistered = true;
        }
        SocialTick();
        CreativeBuild();
        NPC.TargetClosest(false);
        Player player = Main.player[NPC.target];
        if (!player.active || player.dead)
        {
            NPC.velocity.Y += 0.1f;
            return;
        }

        int flockSlot = NPC.whoAmI % 7 - 3;
        Vector2 perch = player.Center + new Vector2(player.direction * (-42f + flockSlot * 28f), -54f - Math.Abs(flockSlot) * 14f);
        Vector2 offset = perch - NPC.Center;
        float distance = offset.Length();
        if (distance > 700f)
        {
            NPC.Center = perch;
            NPC.velocity = Vector2.Zero;
            NPC.netUpdate = true;
            return;
        }

        if (distance > 18f)
        {
            Vector2 desired = offset.SafeNormalize(Vector2.Zero) * MathHelper.Clamp(distance * 0.08f, 1.2f, 7f);
            NPC.velocity = Vector2.Lerp(NPC.velocity, desired, 0.12f);
        }
        else
        {
            NPC.velocity *= 0.82f;
        }

        NPC.spriteDirection = NPC.velocity.X < -0.1f ? -1 : NPC.velocity.X > 0.1f ? 1 : NPC.spriteDirection;
        NPC.rotation = NPC.velocity.X * 0.025f;
    }
}








