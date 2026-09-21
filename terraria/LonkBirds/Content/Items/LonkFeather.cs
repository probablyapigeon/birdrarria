using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace LonkBirds.Content.Items;

public sealed class LonkFeather : ModItem
{
    public override string Texture => "Terraria/Images/Item_" + ItemID.Feather;

    public override void SetDefaults()
    {
        Item.CloneDefaults(ItemID.BirdStatue);
        Item.useStyle = ItemUseStyleID.HoldUp;
        Item.useTime = 20;
        Item.useAnimation = 20;
        Item.consumable = false;
        Item.maxStack = 1;
        Item.value = Item.buyPrice(silver: 25);
        Item.rare = ItemRarityID.Blue;
        Item.UseSound = SoundID.Item44;
    }

    public override bool? UseItem(Player player)
    {
        if (Main.netMode == NetmodeID.MultiplayerClient)
            return true;

        int index = NPC.NewNPC(player.GetSource_ItemUse(Item), (int)player.Center.X,
            (int)player.Center.Y - 48, ModContent.NPCType<NPCs.LonkBirdNPC>());
        if (index < Main.maxNPCs)
        {
            Main.npc[index].netUpdate = true;
            if (Main.netMode == NetmodeID.Server)
                NetMessage.SendData(MessageID.SyncNPC, number: index);
        }
        return true;
    }

    public override void AddRecipes()
    {
        Recipe recipe = CreateRecipe();
        recipe.AddIngredient(ItemID.Wood, 10);
        recipe.AddTile(TileID.WorkBenches);
        recipe.Register();
    }
}


