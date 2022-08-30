# bot.py
import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from utils import get_mean_color_by_url, process_roll
from requests.exceptions import HTTPError
from invitation_message_pairs import InvitationMessagePairs

import configparser
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf8')

ERROR_PREFIX = config['ERROR']['ERROR_PREFIX']

PRIMARY_COLOR = int(config['STYLE']['PRIMARY_COLOR'], 0)
ERROR_COLOR = int(config['STYLE']['ERROR_COLOR'], 0)
VOTE_EMOJI = '\U00002705'

ROLE_ADMIN = config['ROLE']['ROLE_ADMIN']
ROLE_DM = config['ROLE']['ROLE_DM']

CATEGORY_CHANNEL_GALLERY = config['CATEGORIES']['CATEGORY_CHANNEL_GALLERY']
CATEGORY_MAIN_CHANNELS = config['CATEGORIES']['CATEGORY_MAIN_CHANNELS']

CHANNEL_CAMPAIGNS_GALLERY = config['CHANNELS']['CHANNEL_CAMPAIGNS_GALLERY']
CHANNEL_MAIN_GALLERY = config['CHANNELS']['CHANNEL_MAIN_GALLERY']
CHANNEL_DEFAULT_VOICE = config['CHANNELS']['CHANNEL_DEFAULT_VOICE']
CHANNEL_DEFAULT_TEXT = config['CHANNELS']['CHANNEL_DEFAULT_TEXT']
CHANNEL_DEFAULT_ANNOUNCEMENTS = config['CHANNELS']['CHANNEL_DEFAULT_ANNOUNCEMENTS']

imp_main = InvitationMessagePairs('./imp/imp_main.json')
imp_campaign = InvitationMessagePairs('./imp/imp_campaign.json')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.slash_command(name='create_channel', description="Создать новый канал")
async def create_channel(ctx, name: str, description: str = '', logo: disnake.Attachment = None):
    """
    Create new channel

    Parameters
    ----------
    name: Название канала
    description: Короткое описание канала
    logo: Лого компании, которое будет отображаться в галлерее каналов
    """

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    main_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_MAIN_CHANNELS)
    existing_channel = disnake.utils.get(main_category.channels, name=name)
    if not existing_channel:
        channel = await ctx.guild.create_text_channel(name, category=main_category, reason=None)
        info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_MAIN_GALLERY)
        embedVar = disnake.Embed(title=name, description=description, color=PRIMARY_COLOR)
        if logo:
            try:
                mean_color = get_mean_color_by_url(logo.url)
                embedVar.color = mean_color[0] * 16**4 + mean_color[1] * 16**2 + mean_color[2]
                embedVar.set_thumbnail(url=logo.url)
            except HTTPError as http_err:
                error_embed = disnake.Embed(title='Ошибка связи с высшими силами', description=http_err, color=ERROR_COLOR)
                await ctx.channel.send(embed=error_embed)
            except Exception as err:
                error_embed = disnake.Embed(title='Ошибка', description=err, color=ERROR_COLOR)
                await ctx.channel.send(embed=error_embed)
        author_name = ctx.author.nick if ctx.author.nick else ctx.author.display_name
        if ctx.author.avatar:
            embedVar.set_author(name=author_name, icon_url=ctx.author.avatar.url)
        else:
            embedVar.set_author(name=author_name)
        message = await info_channel.send(embed=embedVar)
        await message.add_reaction(VOTE_EMOJI) 
        imp_main.add_pair(message.id, channel.id)
        await ctx.edit_original_message(f'Канал **{name}** создан.')

@bot.slash_command(name='create_campaign', description="Создать новую компанию")
#@commands.has_role(ROLE_ADMIN)
async def create_campaign(ctx, name: str, description: str = '', logo: disnake.Attachment = None):
    """
    Create new campaign group and three default channels

    Parameters
    ----------
    name: Название компании
    description: Короткое описание компании
    logo: Лого компании, которое будет отображаться в галлерее компаний
    """

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    category_overwrites = {
        ctx.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
        ctx.author: disnake.PermissionOverwrite(read_messages=True, manage_channels=True,
         manage_roles=True, manage_messages=True, priority_speaker=True, mute_members=True,
         deafen_members=True, move_members=True)
    }
    existing_category = disnake.utils.get(ctx.guild.categories, name=name)
    if not existing_category:
        category = await ctx.guild.create_category(name, overwrites=category_overwrites, reason=None)
        await ctx.guild.create_text_channel(CHANNEL_DEFAULT_ANNOUNCEMENTS, category=category, reason=None)
        await ctx.guild.create_text_channel(CHANNEL_DEFAULT_TEXT, category=category, reason=None)
        await ctx.guild.create_voice_channel(CHANNEL_DEFAULT_VOICE, category=category, reason=None)
        info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_CAMPAIGNS_GALLERY)
        embedVar = disnake.Embed(title=name, description=description, color=PRIMARY_COLOR)
        if logo:
            try:
                mean_color = get_mean_color_by_url(logo.url)
                embedVar.color = mean_color[0] * 16**4 + mean_color[1] * 16**2 + mean_color[2]
                embedVar.set_thumbnail(url=logo.url)
            except HTTPError as http_err:
                error_embed = disnake.Embed(title='Ошибка связи с высшими силами', description=http_err, color=ERROR_COLOR)
                await ctx.channel.send(embed=error_embed)
            except Exception as err:
                error_embed = disnake.Embed(title='Ошибка', description=err, color=ERROR_COLOR)
                await ctx.channel.send(embed=error_embed)
        author_name = ctx.author.nick if ctx.author.nick else ctx.author.display_name
        if ctx.author.avatar:
            embedVar.set_author(name=author_name, icon_url=ctx.author.avatar.url)
        else:
            embedVar.set_author(name=author_name)
        message = await info_channel.send(embed=embedVar)
        await message.add_reaction(VOTE_EMOJI) 
        imp_campaign.add_pair(message.id, category.id)
        await ctx.edit_original_message(f'Группа для компании **{name}** создана.')
    else:
        await ctx.edit_original_message(f'Компания **{name}** уже существует.')

@bot.slash_command(name='roll', description="Бросить игральный кости")
async def roll(ctx, src: str):
    """
    Roll virtual dices

    Parameters
    ----------
    src: Формула (Поддерживает математические операции)
    """
    result, msg = process_roll(src)
    if result == 1:
        msg = f'**{ERROR_PREFIX}**: {msg}'
        await ctx.response.send_message(msg)
    elif result == 2:
        error_embed = disnake.Embed(title='Ошибка', description=msg, color=ERROR_COLOR)
        await ctx.response.send_message(embed=error_embed)
    else:
        await ctx.response.send_message(msg)

@bot.slash_command(name='r', description="Бросить игральный кости")
async def r(ctx, src):
    """
    Roll virtual dices

    Parameters
    ----------
    src: Формула (Поддерживает математические операции)
    """

    result, msg = process_roll(src)
    if result == 1:
        msg = f'**{ERROR_PREFIX}**: {msg}'
        await ctx.response.send_message(msg)
    elif result == 2:
        error_embed = disnake.Embed(title='Ошибка', description=msg, color=ERROR_COLOR)
        await ctx.response.send_message(embed=error_embed)
    else:
        await ctx.response.send_message(msg)

async def imp_reaction_update(payload, status: bool):
    if imp_main.contains_message_id(payload.message_id):
        if str(payload.emoji) == VOTE_EMOJI:
            guild = bot.get_guild(payload.guild_id)
            member = await bot.fetch_user(payload.user_id)
            if member != guild.me:
                channel_id = imp_main.get_room_id(payload.message_id)
                channel = disnake.utils.get(guild.channels, id=channel_id)
                await channel.set_permissions(member, read_messages=status)
    elif imp_campaign.contains_message_id(payload.message_id):
        if str(payload.emoji) == VOTE_EMOJI:
            guild = bot.get_guild(payload.guild_id)
            member = await bot.fetch_user(payload.user_id)
            if member != guild.me:
                category_id = imp_campaign.get_room_id(payload.message_id)
                category = disnake.utils.get(guild.categories, id=category_id)
                await category.set_permissions(member, read_messages=status)
        
@bot.event
async def on_raw_reaction_add(payload):
    await imp_reaction_update(payload, True)
    
@bot.event
async def on_raw_reaction_remove(payload):
    await imp_reaction_update(payload, False)
                    
    
@bot.event
async def on_guild_channel_delete(channel):
    gallery_category = disnake.utils.get(channel.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    message_id = imp_main.get_message_id(channel.id) 
    if message_id:
        imp_main.delete_pair(message_id)
        info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_MAIN_GALLERY)
        message = await info_channel.fetch_message(message_id)
        await message.delete()
        return
    message_id = imp_campaign.get_message_id(channel.id)
    if message_id:
        imp_campaign.delete_pair(message_id)
        info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_CAMPAIGNS_GALLERY)
        message = await info_channel.fetch_message(message_id)
        await message.delete()
        return

bot.run(TOKEN)