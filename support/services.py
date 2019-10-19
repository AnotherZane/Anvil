
from database import dbfunctions
from datetime import datetime
from support import config as cfg
import operator
import time
import re
from support import log
logger = log.Logger
from discord.ext import commands


# Search for a specific user and return it
class Search:
    @staticmethod
    def search_user(ctx, search):
        # Search by discord user
        user = next((i for i in ctx.guild.members if str(search).lower() in str(i).lower()), None)
        # Search by discord user nickname
        if user is None:
            user = next((i for i in ctx.guild.members if str(search).lower() in str(i.display_name).lower()), None)
        # Search discord by id
        if user is None and search is not None:
            # Remove all non-numerics
            search = re.sub("[^0-9]", "", search)
            user = next((i for i in ctx.guild.members if search.lower() in str(i.id)), ctx.author)
        elif search is None:
            user = ctx.author
        return user


# Allows for creation of a dict that allows attributes to be called instead of keys
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def difference_in_minutes(d1, d2):
    # Convert to Unix timestamp
    d1_ts = time.mktime(d1.timetuple())
    d2_ts = time.mktime(d2.timetuple())

    # They are now in seconds, subtract and then divide by 60 to get minutes.
    difference = int(d2_ts - d1_ts) / 60
    return difference


def get_roles_by_id(guild, list_roles_id):
    list_roles_objects = []
    for role in list_roles_id:
        # Create role dict with attributes after fetching role object
        x = guild.get_role(int(role.role_id))
        dbrole = AttrDict()
        dbrole.update({"role": x, "point_req": role.point_requirement, "karma_req": role.karma_requirement})
        # Add role dict to list
        list_roles_objects.append(dbrole)
    list_roles_objects = sorted(list_roles_objects, key=operator.itemgetter('point_req', 'karma_req'), reverse=True)
    return list_roles_objects


async def set_user_auto_roles(user, guild):
    # Auto role and user data
    roles_raw = dbfunctions.retrieve_roles(guild.id)
    auto_roles = get_roles_by_id(guild, roles_raw)

    user_data = dbfunctions.retrieve_user(user)
    user_points, user_karma = user_data.activity_points, user_data.karma

    # Role lists
    all_auto_roles = []
    current_roles = user.roles
    allowed_roles = []
    not_allowed_roles = []

    # Check which auto_roles apply to the current user
    for role in auto_roles:
        all_auto_roles.append(role.role)
        if user_points >= role.point_req and user_karma >= role.karma_req:
            allowed_roles.append(role.role)

    # Remove auto roles the user shouldn't have from current_roles
    for role in current_roles.copy():
        if role in all_auto_roles and role not in allowed_roles:
            not_allowed_roles.append(role)
        if role not in allowed_roles:
            current_roles.remove(role)

    # Set up roles to actually add
    for role in allowed_roles.copy():
        if role in current_roles:
            allowed_roles.remove(role)

    # Actually add/remove roles here
    # Add roles first. Might break if missing required perms!
    if bool(allowed_roles):
        try:
            await user.add_roles(*allowed_roles, reason="Automatic role update")
            logger.log(logger.INFO, f"added auto roles to {user}", guild.name)
        except Exception as e:
            logger.log(logger.ERROR, f"couldn't add an auto role to {user} due to: {e}.", guild.name)
    # Removed roles. Might break if missing required perms!
    if bool(not_allowed_roles):
        try:
            await user.remove_roles(*not_allowed_roles, reason="Automatic role update")
            logger.log(logger.INFO, f"removed auto from roles {user}", guild.name)
        except Exception as e:
            logger.log(logger.ERROR, f"couldn't remove an auto role from {user} due to: {e}.", guild.name)


# Takes messages and prints them to the determined log channel in the guild (if it exists)
async def guild_log(arg_guild, arg_content, arg_error):
    # Time logging
    now = datetime.now()
    now_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # Error logging
    if arg_error:
        arg_content += f"\n\nIn this error persists, please notify {cfg.owner}"
    # Fetch log-channel status, if returns true post to there
    guild_data = dbfunctions.retrieve_guild(arg_guild)
    if guild_data.log_channel_id:
        try:
            channel = arg_guild.get_channel(int(guild_data.log_channel_id))
            await channel.send(f"```ini\n[{now_string}]\n{arg_content}\n```")
        except Exception as e:
            logger.log(logger.ERROR, f"{e}")


# Check if user has higher authority level
def authority_check(arg_target_user, arg_user):
    if arg_user.top_role > arg_target_user.top_role:
        return True
    else:
        return False
