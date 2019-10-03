import discord
from discord.ext import commands
from support import config as cfg
from support.services import Search
from support import services
from database import dbfunctions



class General(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.sniped_message = None

    # Commands
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! ({round(self.client.latency * 1000)}ms)')

    @commands.command(aliases=['uinfo', 'ui'])
    async def userinfo(self, ctx, *, user = None):

        # Fetch relevant user and accompanying roles
        user = Search.search_user(ctx, user)
        dbuser = dbfunctions.retrieve_user(user)
        roles = [role for role in user.roles]

        # Create embed
        embed = discord.Embed(colour=user.color, timestamp=ctx.message.created_at, title="*Questions?*", url=cfg.embed_url)
        # Set embed fields and values
        embed.set_author(name=f"{user}")
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=cfg.embed_footer, icon_url=self.client.user.avatar_url)

        embed.add_field(name="ID:", value=user.id, inline=False)
        embed.add_field(name="Created at:", value=user.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=False)
        embed.add_field(name="Joined at:", value=user.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=False)

        embed.add_field(name=f"Roles ({len(roles)}):", value=" ".join([role.mention for role in roles]), inline=False)
        embed.add_field(name="Top role:", value=user.top_role.mention, inline=True)

        embed.add_field(name="Bot?", value=user.bot, inline=True)
        embed.add_field(name="User stats", value=":e_mail: Messages sent: " + str(dbuser.messages_sent) +
                                                 " :speaking_head: Activity: " + str(dbuser.activity_points) +
                                                 " :angel: Karma: " + str(dbuser.karma), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['sinfo', 'si'])
    async def serverinfo(self, ctx):
        # Set up
        roles = [role for role in ctx.guild.roles]
        roles.reverse()
        boosters = [booster for booster in ctx.guild.premium_subscribers]
        boosters.reverse()
        members_total = ctx.guild.members
        members_bots = sum(1 for member in members_total if member.bot is True)
        members_online = sum(1 for member in members_total if member.bot is False and member.status is not discord.Status.offline)
        members_offline = len(members_total) - members_bots - members_online

        # Create embed
        embed = discord.Embed(colour=self.client.user.color, timestamp=ctx.message.created_at, title="*Questions?*",
                              url=cfg.embed_url)
        # Set embed defaults
        embed.set_author(name=f"{ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text=cfg.embed_footer, icon_url=self.client.user.avatar_url)

        # Set fields
        embed.add_field(name=f"Members: ({len(members_total)})", value=f"<:greendot:617798086403686432>{members_online} - <:reddot:617798085938118730>{members_offline} - 🤖 {members_bots}")
        embed.add_field(name="Created at:", value=ctx.guild.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
        embed.add_field(name=f"Roles ({len(roles)}):", value=" ".join([role.mention for role in roles]))
        # Show nitro boosters
        if not boosters:
            embed.add_field(name=f"Nitro boosters (0)", value="None ")
        else:
            embed.add_field(name=f"Nitro boosters ({len(boosters)})", value=" ".join([booster.mention for booster in boosters]))
        await ctx.send(embed=embed)

    # Snipe command set up
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.sniped_message = message

    @commands.command()
    async def snipe(self, ctx):
        if self.sniped_message is None:
            await ctx.send("Nothing to be sniped.")
        else:
            embed = discord.Embed(colour=self.sniped_message.author.color, timestamp=self.sniped_message.created_at)
            embed.set_thumbnail(url=self.sniped_message.author.avatar_url)
            embed.set_footer(text=cfg.embed_footer, icon_url=self.client.user.avatar_url)
            embed.add_field(name=f"{self.sniped_message.author} said:", value=self.sniped_message.content)
            await ctx.send(embed=embed)

    @commands.command()
    async def roles(self, ctx):
        roles_raw = dbfunctions.retrieve_roles(ctx.guild.id)
        roles = services.get_roles_by_id(ctx.guild, roles_raw)
        roles_string = ""
        for role in roles:
            roles_string += role.role.mention
            if role.point_req > 0:
                roles_string += "\n Points: " + str(role.point_req)
            if role.karma_req > 0:
                roles_string += "\n Karma: " + str(role.karma_req)
            roles_string += "\n\n"

        # Create embed
        embed = discord.Embed(colour=self.client.user.color, timestamp=ctx.message.created_at, title="*Questions?*",
                              url=cfg.embed_url)
        # Set embed defaults
        embed.set_author(name=f"{ctx.guild.name} - Role Requirements")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text=cfg.embed_footer, icon_url=self.client.user.avatar_url)

        # Set fields
        embed.add_field(name=f"Roles({len(roles)}):", value=roles_string)

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(General(client))