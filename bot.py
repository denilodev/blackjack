import discord
from discord.ext import commands
from discord import app_commands
import random
from keys import DISCORD_TOKEN, GUILD_ID

GUILD_TEST = discord.Object(id=GUILD_ID)

cards = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
suits = ['♧', '♢', '♡', '♤']
full_deck = [f"{card}{suit}" for suit in suits for card in cards]

BLACKJACK = 21
DEALER_MINIMUM = 16

def hit_card(deck, hand):
    card = random.choice(deck)
    hand.append(card)
    deck.remove(card)

def calculate_hand(hand):
    total = 0
    ace_11s = 0
    for card in hand:
        value = card[:-1]
        if value.isdigit():
            total += int(value)
        elif value in ['J', 'Q', 'K']:
            total += 10
        else:
            total += 11
            ace_11s += 1
    while ace_11s and total > 21:
        total -= 10
        ace_11s -= 1
    return total

def show_hand(hand):
    text = str(hand[0])
    for card in hand[1:]:
        text = text + ' | ' + str(card)
    return text

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        # Sync with the guild to 
        try:
            synced = await self.tree.sync(guild=GUILD_TEST)
            print(f'Synced {len(synced)} command(s) to guild {GUILD_TEST.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)


@client.tree.command(name="bj", description="Play Blackjack", guild=GUILD_TEST)
async def embed(interaction: discord.Interaction, bet: int):
    embed = discord.Embed(title="Blackjack", description=f"{interaction.user} has bet {bet} coins", color=discord.Colour.dark_grey())
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
    update = await interaction.response.edit_message(embed=embed)
    deck = full_deck
    player_hand = []
    dealer_hand = []
    for _ in range(2):
        hit_card(deck, dealer_hand)
        hit_card(deck, player_hand)
    
    # Check if player got blackjack immediately
    if calculate_hand(player_hand) == BLACKJACK:
        if calculate_hand(dealer_hand) == BLACKJACK:
            embed.description = "DOUBLE BLACKJACK! DRAW!"
            embed.add_field(name=f"Player's hand ({BLACKJACK})", value=f"{show_hand(player_hand)}", inline=False)
            embed.add_field(name=f"Dealer's hand ({BLACKJACK})", value=f"{show_hand(dealer_hand)}", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            embed.description = "BLACKJACK! PLAYER WON!"
            embed.add_field(name=f"Player's hand ({BLACKJACK})", value=f"{show_hand(player_hand)}", inline=False)
            embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand)})", value=f"{show_hand(dealer_hand)}", inline=False)
            await interaction.response.send_message(embed=embed)
    else:
        embed.add_field(name=f"Player's hand ({calculate_hand(player_hand)})", value=f"{show_hand(player_hand)}", inline=False)
        embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand[:1])}+?)", value=f"{dealer_hand[0]} | ??", inline=False)
        
        def dealer_turn():
            while calculate_hand(dealer_hand) < DEALER_MINIMUM:
                hit_card(deck, dealer_hand)
            return calculate_hand(dealer_hand)

        def is_player_busted():
            # Check if player busted
            if calculate_hand(player_hand) > BLACKJACK:
                embed.description = "PLAYER BUSTED! DEALER WON!"
                embed.add_field(name=f"Player's hand ({calculate_hand(player_hand)})", value=f"{show_hand(player_hand)}", inline=False)
                embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand)})", value=f"{show_hand(dealer_hand)}", inline=False)
                return True
            # Game goes on
            else:
                return False
        
        def is_player_blackjack():
            # Check if player got blackjack
            if calculate_hand(player_hand) == BLACKJACK:
                if dealer_turn() == BLACKJACK:
                    embed.description = "DOUBLE BLACKJACK! DRAW!"
                    embed.add_field(name=f"Player's hand ({BLACKJACK})", value=f"{show_hand(player_hand)}", inline=False)
                    embed.add_field(name=f"Dealer's hand ({BLACKJACK})", value=f"{show_hand(dealer_hand)}", inline=False)
                    return True
                else:
                    embed.description = "BLACKJACK! PLAYER WON!"
                    embed.add_field(name=f"Player's hand ({BLACKJACK})", value=f"{show_hand(player_hand)}", inline=False)
                    embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand)})", value=f"{show_hand(dealer_hand)}", inline=False)
                    return True
            else:
                return False
        
        def endgame():
            embed.add_field(name=f"Player's hand ({calculate_hand(player_hand)})", value=f"{show_hand(player_hand)}", inline=False)
            embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand)})", value=f"{show_hand(dealer_hand)}", inline=False)

        # Buttons
        class View(discord.ui.View):
            # Hit button
            @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="🃏")
            async def hit_button(self, button: discord.Button, interac: discord.Interaction):

                # Only the player can interact
                if button.user.id != interaction.user.id:
                    return
                
                embed.clear_fields()
                hit_card(deck, player_hand)
                if is_player_busted() or is_player_blackjack():
                    await button.response.edit_message(embed=embed, view=None)
                else:
                    embed.add_field(name=f"Player's hand ({calculate_hand(player_hand)})", value=f"{show_hand(player_hand)}", inline=False)
                    embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand[:1])}+?)", value=f"{dealer_hand[0]} | ??", inline=False)
                    await button.response.edit_message(embed=embed)

            # Stand button
            @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray, emoji="🛑")
            async def stand_button(self, button: discord.Button, interac: discord.Interaction):

                # Only the player can interact
                if button.user.id != interaction.user.id:
                    return
                
                embed.clear_fields()
                dealer_final = dealer_turn()
                player_final = calculate_hand(player_hand)
                if dealer_final > BLACKJACK:
                    embed.description = "DEALER BUSTED! PLAYER WON!"
                elif dealer_final > player_final:
                    embed.description = "DEALER WON!"
                elif player_final > dealer_final:
                    embed.description = "PLAYER WON!"
                else:
                    embed.description = "DRAW!"
                embed.add_field(name=f"Player's hand ({calculate_hand(player_hand)})", value=f"{show_hand(player_hand)}", inline=False)
                embed.add_field(name=f"Dealer's hand ({calculate_hand(dealer_hand)})", value=f"{show_hand(dealer_hand)}", inline=False)
                await button.response.edit_message(embed=embed, view=None)
        await interaction.response.send_message(embed=embed, view=View())

client.run(DISCORD_TOKEN)