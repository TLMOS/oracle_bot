import os
import configparser
import random

import disnake
from disnake.ext import commands
from requests.exceptions import HTTPError

from utils import get_mean_color_by_url, process_roll
from room_manager import RoomManager

# from dotenv import load_dotenv
# load_dotenv()

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf8')

ERROR_PREFIX = config['ERROR']['ERROR_PREFIX']

PRIMARY_COLOR = int(config['STYLE']['PRIMARY_COLOR'], 0)
ERROR_COLOR = int(config['STYLE']['ERROR_COLOR'], 0)
WARNING_COLOR = int(config['STYLE']['WARNING_COLOR'], 0)
VOTE_EMOJI = '\U00002705'

ROLE_ADMIN = config['ROLE']['ROLE_ADMIN']
ROLE_DM = config['ROLE']['ROLE_DM']

CATEGORY_CHANNEL_GALLERY = config['CATEGORIES']['CATEGORY_CHANNEL_GALLERY']
CATEGORY_GENERAL_CHANNELS = config['CATEGORIES']['CATEGORY_GENERAL_CHANNELS']

CHANNEL_CAMPAIGNS_GALLERY = config['CHANNELS']['CHANNEL_CAMPAIGNS_GALLERY']
CHANNEL_GENERAL_GALLERY = config['CHANNELS']['CHANNEL_GENERAL_GALLERY']
CHANNEL_DEFAULT_VOICE = config['CHANNELS']['CHANNEL_DEFAULT_VOICE']
CHANNEL_DEFAULT_TEXT = config['CHANNELS']['CHANNEL_DEFAULT_TEXT']
CHANNEL_DEFAULT_ANNOUNCEMENTS = config['CHANNELS']['CHANNEL_DEFAULT_ANNOUNCEMENTS']

ROOM_TABLE_GENERAL = 'general'
ROOM_TABLE_CAMAPIGN = 'campaign'

if not os.path.isdir('./database'):
    os.mkdir('./database')
room_manager = RoomManager('./database/oracle.db')

TOKEN = os.getenv('DISCORD_TOKEN')

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

async def create_room_card(ctx, title, description, logo):
    embed = disnake.Embed(title=title, description=description, color=PRIMARY_COLOR)
    if logo:
        try:
            mean_color = get_mean_color_by_url(logo.url)
            embed.color = mean_color[0] * 16**4 + mean_color[1] * 16**2 + mean_color[2]
            embed.set_thumbnail(url=logo.url)
        except HTTPError as http_err:
            error_embed = disnake.Embed(title='Ошибка связи с высшими силами',
                description=http_err, color=ERROR_COLOR)
            await ctx.channel.send(embed=error_embed)
    author_name = ctx.author.nick if ctx.author.nick else ctx.author.display_name
    if ctx.author.avatar:
        embed.set_author(name=author_name, icon_url=ctx.author.avatar.url)
    else:
        embed.set_author(name=author_name)
    return embed

@bot.slash_command(name='create_channel', description="Создать новый канал")
async def create_channel(ctx, title: str, description: str = '', private: bool = False,
 logo: disnake.Attachment = None):
    """
    Create new channel

    Parameters
    ----------
    title: Название канала
    description: Короткое описание канала
    private: Приватный канал не будет иметь картотчку в галлерее
    logo: Лого канала, которое будет отображаться в галлерее каналов
    """

    channel_overwrites = {
        ctx.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
        ctx.author: disnake.PermissionOverwrite(read_messages=True, manage_channels=True,
        manage_roles=True, manage_messages=True)
    }

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    general_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_GENERAL_CHANNELS)
    existing_channel = disnake.utils.get(general_category.channels, name=title)
    if not existing_channel:
        channel = await ctx.guild.create_text_channel(title, category=general_category,
         overwrites=channel_overwrites, reason=None)
        if private:
            await ctx.delete_original_message()
        else:
            embed = await create_room_card(ctx, title, description, logo)
            info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_GENERAL_GALLERY)
            message = await info_channel.send(embed=embed)
            await message.add_reaction(VOTE_EMOJI)
            room_manager.add_room(ROOM_TABLE_GENERAL, channel.id, message.id, ctx.author.id)
            await ctx.edit_original_message(f'Канал **{title}** создан.')

@bot.slash_command(name='create_campaign', description="Создать новую кампанию")
#@commands.has_role(ROLE_ADMIN)
async def create_campaign(ctx, title: str, description: str = '', private: bool = False,
 logo: disnake.Attachment = None):
    """
    Create new campaign group and three default channels

    Parameters
    ----------
    title: Название кампании
    description: Короткое описание кампании
    private: Приватная компания не будет иметь картотчку в галлерее
    logo: Лого кампании, которое будет отображаться в галлерее кампаний
    """

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    category_overwrites = {
        ctx.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
        ctx.author: disnake.PermissionOverwrite(read_messages=True, manage_channels=True,
         manage_roles=True, manage_messages=True, priority_speaker=True, mute_members=True,
         deafen_members=True, move_members=True)
    }
    existing_category = disnake.utils.get(ctx.guild.categories, name=title)
    if not existing_category:
        category = await ctx.guild.create_category(title, overwrites=category_overwrites, reason=None)
        await ctx.guild.create_text_channel(CHANNEL_DEFAULT_ANNOUNCEMENTS, category=category, reason=None)
        await ctx.guild.create_text_channel(CHANNEL_DEFAULT_TEXT, category=category, reason=None)
        await ctx.guild.create_voice_channel(CHANNEL_DEFAULT_VOICE, category=category, reason=None)
        if private:
            await ctx.delete_original_message()
        else:
            embed = await create_room_card(ctx, title, description, logo)
            info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_CAMPAIGNS_GALLERY)
            message = await info_channel.send(embed=embed)
            await message.add_reaction(VOTE_EMOJI)
            room_manager.add_room(ROOM_TABLE_CAMAPIGN, category.id, message.id, ctx.author.id)
        await ctx.edit_original_message(f'Группа для кампании **{title}** создана.')
    else:
        await ctx.edit_original_message(f'Кампания **{title}** уже существует.')

@bot.slash_command(name='edit_channel', description="Отредактировать карточку канала")
async def edit_channel(ctx, title: str, new_title: str = '', new_description: str = '',
 new_logo: disnake.Attachment = None):
    """
    Edit channel card

    Parameters
    ----------
    title: Название канала
    new_title: Новое название канала
    new_description: Новое  описание канала
    new_logo: Новое лого канала
    """

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    general_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_GENERAL_CHANNELS)
    existing_channel = disnake.utils.get(general_category.channels, name=title)
    if existing_channel:
        room = room_manager.get_room_by_cid(ROOM_TABLE_GENERAL, existing_channel.id)
        if room:
            if room.author_id == ctx.author.id:
                await existing_channel.edit(name=new_title)
                embed = await create_room_card(ctx, new_title, new_description, new_logo)
                info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_GENERAL_GALLERY)
                message = await info_channel.fetch_message(room.message_id)
                await message.edit(embed=embed)
                await ctx.edit_original_message(f'Канал **{title}** отредактиврован.')
            else:
                await ctx.edit_original_message('Только создатель канала имеет право на редактирование.')
        else:
            await ctx.edit_original_message(f'Канал **{title}** не имеет карточки.')
    else:
        await ctx.edit_original_message(f'Канал **{title}** не найден.')

@bot.slash_command(name='edit_campaign', description="Отредактировать карточку канала")
async def edit_campaign(ctx, title: str, new_title: str = '', new_description: str = '',
 new_logo: disnake.Attachment = None):
    """
    Edit campaign card

    Parameters
    ----------
    title: Название кампании
    new_title: Новое название кампании
    new_description: Новое  описание кампании
    new_logo: Новое лого кампании
    """

    await ctx.response.defer()
    gallery_category = disnake.utils.get(ctx.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    existing_category = disnake.utils.get(ctx.guild.categories, name=title)
    if existing_category:
        room = room_manager.get_room_by_cid(ROOM_TABLE_CAMAPIGN, existing_category.id)
        if room:
            if room.author_id == ctx.author.id:
                await existing_category.edit(name=new_title)
                embed = await create_room_card(ctx, new_title, new_description, new_logo)
                info_channel = disnake.utils.get(gallery_category.channels, name=CHANNEL_CAMPAIGNS_GALLERY)
                message = await info_channel.fetch_message(room.message_id)
                await message.edit(embed=embed)
                await ctx.edit_original_message(f'Кампания **{title}** отредактиврована.')
            else:
                await ctx.edit_original_message('Только создатель канала имеет право на редактирование.')
        else:
            await ctx.edit_original_message(f'Канал **{title}** не имеет карточки.')
    else:
        await ctx.edit_original_message(f'Канал **{title}** не найден.')

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

@bot.slash_command(name='roll_ability_scores',
 description="Пробросить характеристики для dnd-подобных систем")
async def roll_ability_scores(ctx):
    """
    Roll dnd ability scores
    """

    abilities = [sum(sorted([random.randint(1, 6) for j in range(4)])[1:]) for i in range(6)]
    msg = f'`{", ".join(map(str,abilities))}`'
    if min(abilities) <= 5:
        msg += '\n*Well, fuck...*'
    elif sum(abilities) > 70 and 18 in abilities:
        msg += '\n*Feeling lucky?*'
    if sum(abilities) > 70:
        embed = disnake.Embed(title='Характеристики', description=msg, color=PRIMARY_COLOR)
    else:
        msg += '\n*Сумма характеристик меньше 70!*'
        embed = disnake.Embed(title='Характеристики', description=msg, color=WARNING_COLOR)
    await ctx.response.send_message(embed=embed)

async def room_reaction_update(payload, status: bool):
    if str(payload.emoji) == VOTE_EMOJI:
        for table in [ROOM_TABLE_GENERAL, ROOM_TABLE_CAMAPIGN]:
            room = room_manager.get_room_by_mid(table, payload.message_id)
            if room and payload.user_id != room.author_id:
                guild = bot.get_guild(payload.guild_id)
                member = await bot.fetch_user(payload.user_id)
                if member != guild.me:
                    channel = disnake.utils.get(guild.channels, id=room.channel_id)
                    await channel.set_permissions(member, read_messages=status)

@bot.event
async def on_raw_reaction_add(payload):
    await room_reaction_update(payload, True)

@bot.event
async def on_raw_reaction_remove(payload):
    await room_reaction_update(payload, False)

@bot.event
async def on_guild_channel_delete(channel):
    gallery_category = disnake.utils.get(channel.guild.categories, name=CATEGORY_CHANNEL_GALLERY)
    for (table, gallery_channel) in [(ROOM_TABLE_GENERAL, CHANNEL_GENERAL_GALLERY),
     (ROOM_TABLE_CAMAPIGN, CHANNEL_CAMPAIGNS_GALLERY)]:
        room = room_manager.get_room_by_cid(table, channel.id)
        if room:
            room_manager.delete_room(table, room)
            info_channel = disnake.utils.get(gallery_category.channels, name=gallery_channel)
            message = await info_channel.fetch_message(room.message_id)
            await message.delete()
            return

bot.run(TOKEN)
