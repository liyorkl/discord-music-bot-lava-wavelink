import discord
import wavelink
from discord import app_commands
from discord.ext import commands

import secrets_me


class Bot(commands.Bot):

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents, command_prefix='!')

    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')

    # async def on_wavelink_track_start(payload: wavelink.TrackStartEventPayload):
    #     print(payload.track.title)
    #     print(payload.original.title)
    #     track = payload.track
    #     channel = payload.player.channel
    #     embedMessage = discord.Embed(
    #         title="Music on!!!",
    #         description=f"Played ***{track.title}*** by **{track.author}** in **{channel}** channel", color=discord.Color.blue())
    #     embedMessage.set_author(
    #         name=vc.author.display_name + " | Using Azzy's Music Bot", icon_url=vc.author.display_avatar)
    #     embedMessage.set_thumbnail(url=track.artwork)
    #     await vc.channel.send(embed=embedMessage)


bot = Bot()


class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()


@bot.event
async def on_ready():
    bot.loop.create_task(connect_nodes())


async def connect_nodes():
    await bot.wait_until_ready()
    node: wavelink.Node = wavelink.Node(
        uri='http://127.0.0.1:2333', password='youshallnotpass', identifier="Azzy Bot")
    # await bot.tree.sync()
    await wavelink.Pool.connect(client=bot, nodes=[node])


@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f'Node : <{payload.node.identifier}> is ready!')


# @commands.Cog.listener()
# async def on_wavelink_track_start(payload: wavelink.TrackStartEventPayload):
#     print(payload.track.title)
#     print(payload.original.title)
#     track = payload.track
#     channel = payload.player.channel
#     embedMessage = discord.Embed(
#         title="Music on!!!",
#         description=f"Played ***{track.title}*** by **{track.author}** in **{channel}** channel", color=discord.Color.blue())
#     embedMessage.set_author(
#         name=vc.author.display_name + " | Using Azzy's Music Bot", icon_url=vc.author.display_avatar)
#     embedMessage.set_thumbnail(url=track.artwork)
#     await vc.channel.send(embed=embedMessage)


@bot.command()
async def connect(ctx: commands.Context):
    vc = ctx.voice_client
    try:
        channel = ctx.author.voice.channel
    except AttributeError:
        return await ctx.send("Join a voice channel boya!")

    if not vc:
        await ctx.author.voice.channel.connect(cls=CustomPlayer())
    else:
        await ctx.send("The bot is already connected to another voice channel")


@bot.command()
async def disconnect(ctx: commands.Context):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel")


@bot.command()
async def play(ctx: commands.Context, *, query: str) -> None:

    vc = ctx.voice_client
    if not vc:
        custom_player = CustomPlayer()
        vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

    vc.autoplay = wavelink.AutoPlayMode.partial

    tracks = await wavelink.Playable.search(
        query, source=wavelink.TrackSource.YouTubeMusic)

    if not tracks:
        # No tracks found, do something?
        await ctx.send("No Tracks found!")
        return

    # ask the user to select a track
    list_of_tracks = ""
    for i, track in enumerate(tracks):
        list_of_tracks = list_of_tracks + \
            f"{i+1}. {track.title} by {track.author}\n"
        if i == 4:
            embedMessage = discord.Embed(
                title="Select a track by entering the number:",
                description=list_of_tracks, color=discord.Color.blue())
            embedMessage.set_author(
                name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embedMessage)
            break

    trackNum = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    while not trackNum.content.isdigit() or int(trackNum.content) > 5 or int(trackNum.content) < 1:
        await ctx.send("Please enter a valid number between 1 and 5")
        trackNum = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    track = tracks[int(trackNum.content) - 1]

    if not vc.playing:

        await vc.pause(False)
        await vc.play(track)
        embedMessage = discord.Embed(
            title="Music on!!!",
            description=f"Played ***{track.title}*** by **{track.author}** in **{vc.channel}** channel", color=discord.Color.blue())
        embedMessage.set_author(
            name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
        embedMessage.set_thumbnail(url=track.artwork)
        await ctx.send(embed=embedMessage)

    else:
        await vc.queue.put_wait(track)
        embedMessage = discord.Embed(
            title="Music Queued!!!",
            description=f"Queued ***{track.title}*** by **{track.author}** in **{vc.channel}** channel", color=discord.Color.blue())
        embedMessage.set_author(
            name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
        embedMessage.set_thumbnail(url=track.artwork)
        await ctx.send(embed=embedMessage)


@bot.command()
async def p(ctx: commands.Context, *, search: str) -> None:
    await play(ctx, query=search)


@bot.command()
async def stop(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.pause(True)
    embedMessage = discord.Embed(
        title="Music Pasued!!!",
        description=f"***{vc.current.title}*** paused", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@bot.command()
async def pause(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.pause(True)
    embedMessage = discord.Embed(
        title="Music Paused!!!",
        description=f"***{vc.current.title}*** paused", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@bot.command()
async def resume(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.pause(False)
    embedMessage = discord.Embed(
        title="Music Resumed!!!",
        description=f"***{vc.current.title}*** Resumed", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@bot.command()
async def skip(ctx: commands.Context):
    vc = ctx.voice_client
    embedMessage = discord.Embed(
        title="Music Skipped!!!",
        description=f"***{vc.current.title}*** Skipped", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)
    await vc.stop()
    await vc.pause(False)


@bot.command()
async def queue(ctx: commands.Context):
    vc = ctx.voice_client
    stringBuilder = f"Currently playing ***{vc.current.title}***\n\n"
    stringBuilder += f"Current Queue in **{vc.channel}** channel:\n"
    index = 0
    for track in vc.queue:
        stringBuilder += f"*{index+1}*. Song: ***{track.title}***, Artist: **{track.artists[0]}** \n"
        index += 1
    embedMessage = discord.Embed(
        title="Music Queue!!!",
        description=f"{stringBuilder}", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@bot.command()
async def q(ctx: commands.Context):
    await queue(ctx)


@bot.command()
async def remove(ctx: commands.Context, *, trackNum: str):
    vc = ctx.voice_client
    trackNum = int(trackNum) - 1
    embedMessage = discord.Embed(
        title="Music Removed!!!",
        description=f"***{vc.queue[trackNum].title}*** Removed", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)
    del vc.queue[trackNum]

bot.run(secrets_me.token)
