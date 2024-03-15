import discord
import wavelink
import SpotifyHelper
from wavelink.ext import spotify
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


client = Bot()


class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()


# check if song played is the actual song listed on spotify
def checkSongIsSame(ctx: commands.Context, track: spotify.SpotifyTrack):
    vc = ctx.voice_client
    if vc.current.title == track.name:
        return True
    else:
        return False


@client.event
async def on_ready():
    client.loop.create_task(connect_nodes())


async def connect_nodes():
    await client.wait_until_ready()
    sc = spotify.SpotifyClient(
        client_id=secrets_me.spotifyID,
        client_secret=secrets_me.spotifySecret
    )
    node: wavelink.Node = wavelink.Node(
        uri='http://127.0.0.1:2333', password='youshallnotpass', id="Azzy Bot")
    # await client.tree.sync()
    await wavelink.NodePool.connect(client=client, nodes=[node], spotify=sc)


@client.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node : <{node.id}> is ready!')


@client.command()
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


@client.command()
async def disconnect(ctx: commands.Context):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel")


@client.command()
async def play(ctx: commands.Context, *, search: str) -> None:

    vc = ctx.voice_client
    if not vc:
        custom_player = CustomPlayer()
        vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

    vc.autoplay = True

    trackUrl = SpotifyHelper.searcher(search)

    tracks: spotify.SpotifyTrack = await spotify.SpotifyTrack.search(trackUrl)

    if not tracks:
        # No tracks found, do something?
        await ctx.send("No Tracks found!")
        return

    track: spotify.SpotifyTrack = tracks[0]

    if not vc.is_playing():

        await vc.play(track)

        print(checkSongIsSame(ctx, track))

        embedMessage = discord.Embed(
            title="Music on!!!",
            description=f"Played ***{track.name}*** by **{track.artists[0]}** in **{vc.channel}** channel", color=discord.Color.blue())
        embedMessage.set_author(
            name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
        tackimages = track.images
        embedMessage.set_thumbnail(url=tackimages[0])
        await ctx.send(embed=embedMessage)

    else:
        await vc.queue.put_wait(track)

        embedMessage = discord.Embed(
            title="Music Queued!!!",
            description=f"Queued ***{track.name}*** by **{track.artists[0]}** in **{vc.channel}** channel", color=discord.Color.blue())
        embedMessage.set_author(
            name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
        tackimages = track.images
        embedMessage.set_thumbnail(url=tackimages[0])
        await ctx.send(embed=embedMessage)


@client.command()
async def p(ctx: commands.Context, *, search: str) -> None:
    play(ctx, search)


@client.command()
async def stop(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.pause()
    embedMessage = discord.Embed(
        title="Music Pasued!!!",
        description=f"***{vc.current.title}*** paused", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@client.command()
async def pause(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.pause()
    embedMessage = discord.Embed(
        title="Music Paused!!!",
        description=f"***{vc.current.title}*** paused", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@client.command()
async def resume(ctx: commands.Context):
    vc = ctx.voice_client
    await vc.resume()
    embedMessage = discord.Embed(
        title="Music Resumed!!!",
        description=f"***{vc.current.title}*** Resumed", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)


@client.command()
async def skip(ctx: commands.Context):
    vc = ctx.voice_client
    embedMessage = discord.Embed(
        title="Music Skipped!!!",
        description=f"***{vc.current.title}*** Skipped", color=discord.Color.blue())
    embedMessage.set_author(
        name=ctx.author.display_name + " | Using Azzy's Music Bot", icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embedMessage)
    await vc.stop()


@client.command()
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


@client.command()
async def q(ctx: commands.Context):
    queue(ctx)


@client.command()
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

client.run(secrets_me.token)
