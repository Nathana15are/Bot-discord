# bot.py
import discord
from discord.ext import commands
from secret import TOKEN
import json
import asyncio
import os

# =====================
# Charger config
# =====================
if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({"prefix": "!", "theme": "dark", "language": "fr"}, f)

with open("config.json", "r") as f:
    config = json.load(f)

# =====================
# Charger data persistante
# =====================
if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({"warns": {}, "mutes": {}, "bans": {}, "staff": []}, f)

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
warns = data["warns"]
mutes = data["mutes"]
bans = data["bans"]
staff = set(data["staff"])

# =====================
# Bot
# =====================
bot = commands.Bot(command_prefix=config["prefix"], intents=discord.Intents.all())

def save_all():
    data["warns"] = warns
    data["mutes"] = mutes
    data["bans"] = bans
    data["staff"] = list(staff)
    save_data(data)

# =====================
# Embeds selon thème
# =====================
def make_embed(title, description):
    color = discord.Color.dark_grey() if config["theme"]=="dark" else discord.Color.light_grey()
    return discord.Embed(title=title, description=description, color=color)

# =====================
# Vérification staff
# =====================
def is_staff(ctx):
    return ctx.author.id in staff

# =====================
# Commandes setup
# =====================
@bot.command()
async def setup(ctx, option=None, *, value=None):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")

    if option is None:
        await ctx.send("Options disponibles : prefix, theme, language")
        return

    option = option.lower()
    if option == "prefix":
        if not value:
            return await ctx.send("Spécifie le nouveau préfixe !")
        config["prefix"] = value
        bot.command_prefix = value
        with open("config.json", "w") as f:
            json.dump(config, f)
        await ctx.send(f"Préfixe changé en : {value}")

    elif option == "theme":
        if value not in ["dark", "light"]:
            return await ctx.send("Valeur theme : 'dark' ou 'light'")
        config["theme"] = value
        with open("config.json", "w") as f:
            json.dump(config, f)
        await ctx.send(f"Thème changé en : {value}")

    elif option == "language":
        if value not in ["fr", "en"]:
            return await ctx.send("Valeur language : 'fr' ou 'en'")
        config["language"] = value
        with open("config.json", "w") as f:
            json.dump(config, f)
        await ctx.send(f"Langue changée en : {value}")

    else:
        await ctx.send("Option invalide !")

# =====================
# Commandes staff
# =====================
@bot.command()
async def add_staff(ctx, member: discord.Member):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    staff.add(member.id)
    save_all()
    await ctx.send(f"{member} est maintenant staff !")

@bot.command()
async def list_staff(ctx):
    msg = [f"<@{uid}>" for uid in staff]
    await ctx.send(f"Staff : {msg if msg else 'Aucun'}")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason=None):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    warns.setdefault(str(member.id), []).append(reason or "Non précisé")
    save_all()
    await ctx.send(f"{member} a été warn pour : {reason or 'Non précisé'}")

@bot.command()
async def enlever_warn(ctx, member: discord.Member):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    warns.pop(str(member.id), None)
    save_all()
    await ctx.send(f"Tous les warns de {member} ont été enlevés.")

@bot.command()
async def list_warn(ctx, member: discord.Member):
    user_warns = warns.get(str(member.id), [])
    await ctx.send(f"Warns de {member} : {user_warns if user_warns else 'Aucun'}")

@bot.command()
async def mute(ctx, member: discord.Member):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)
    await member.add_roles(role)
    mutes[str(member.id)] = True
    save_all()
    await ctx.send(f"{member} a été mute.")

@bot.command()
async def enlever_mute(ctx, member: discord.Member):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
    mutes.pop(str(member.id), None)
    save_all()
    await ctx.send(f"{member} n'est plus mute.")

@bot.command()
async def list_mute(ctx):
    msg = [f"<@{uid}>" for uid in mutes.keys()]
    await ctx.send(f"Mutes : {msg if msg else 'Aucun'}")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    await member.ban(reason=reason)
    bans[str(member.id)] = reason
    save_all()
    await ctx.send(f"{member} a été ban.")

@bot.command()
async def ban_temp(ctx, member: discord.Member, temps: int, *, reason=None):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    await member.ban(reason=reason)
    bans[str(member.id)] = reason
    save_all()
    await ctx.send(f"{member} a été ban temporairement pour {temps} secondes.")
    await asyncio.sleep(temps)
    await ctx.guild.unban(member)
    bans.pop(str(member.id), None)
    save_all()

@bot.command()
async def enlever_ban(ctx, member: discord.Member):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    bans.pop(str(member.id), None)
    save_all()
    await ctx.send(f"{member} n'est plus ban.")

@bot.command()
async def list_ban(ctx):
    msg = [f"<@{uid}> : {reason}" for uid, reason in bans.items()]
    await ctx.send(f"Bans : {msg if msg else 'Aucun'}")

@bot.command()
async def salons_off(ctx):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Tous les salons ont été fermés.")

@bot.command()
async def salons_on(ctx):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Tous les salons ont été ouverts.")

@bot.command()
async def annonce(ctx, *, message):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    await ctx.send(f"📢 ANNONCE : {message}")

@bot.command()
async def setup_roles(ctx):
    if not is_staff(ctx):
        return await ctx.send("Tu n'as pas la permission !")
    role = discord.utils.get(ctx.guild.roles, name="Staff")
    if not role:
        await ctx.guild.create_role(name="Staff", permissions=discord.Permissions(8))
    muted = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted:
        muted = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted, send_messages=False, speak=False)
    await ctx.send("Setup des rôles terminé !")

# =====================
# Commande ping pour test
# =====================
@bot.command()
async def ping(ctx):
    embed = make_embed("Ping", "Pong