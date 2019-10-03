from database.dbbase import Session
from database.guilds import Guild
from database.users import User
from database.roles import Role
from database.karma import KarmaEvents
from support.services import AttrDict
from datetime import date, datetime
from support import services
from support.bcolors import Bcolors
from sqlalchemy import and_

# Guild updates
def guild_add(guild):
    guild_add_users(guild)
    session = Session()
    guilds = session.query(Guild).all()
    # If new guild
    if sum(str(x.guild_id) == str(guild.id) for x in guilds) is 0:
        new_guild = Guild(guild.name, guild.id, date.today(), '.', True)
        session.add(new_guild)
    # If guild still attached
    elif sum(int(x.id) == 607163424362856458 for x in guild.members) is 1:
        guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
        guild.attached = True
    # If guild left while bot offline
    else:
        guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
        guild.attached = False
    session.commit()
    session.close()


def guild_remove(guild):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    guild.attached = False
    session.commit()
    session.close()


# Set chosen reaction emoji for karma system
def set_guild_karma_emoji(guild, emoji_id):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    guild.karma_emoji = emoji_id
    session.commit()
    session.close()


# Add new users to DB, works both on build and on_guild_join
def guild_add_users(guild):
    # Prep session
    session = Session()
    users = guild.members
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    # Create new users and add them to guild
    for user in users:
        if not user.bot:
            # Check if user already exists for guild
            if sum(str(x.user_id) == str(user.id) for x in guild.users) is 0:
                new_user = User(user.name, user.id, 0, 0, 0)
                guild.users.append(new_user)
                session.add(new_user)
    session.commit()
    session.close()


# Updates amount of messages stored in DB based on arg: increment
def update_user_messages(guild, user, increment):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    user = next((x for x in guild.users if int(x.user_id) == int(user.id)), None)
    user.messages_sent += increment
    session.commit()
    session.close()


# Updates amount of activity points stored in DB based on arg: increment
def update_user_activity(guild, user, increment):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    user = next((x for x in guild.users if int(x.user_id) == int(user.id)), None)
    user.activity_points += increment
    user.last_message = datetime.now()
    session.commit()
    session.close()


# Updates amount of karma stored in DB based on arg: increment
def update_user_karma(guild, user, increment):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild.id).first()
    user = next((x for x in guild.users if int(x.user_id) == int(user.id)), None)
    user.karma += increment
    session.commit()
    session.close()


def set_karma_event(giving_user, receiving_user):
    session = Session()

    # Retrieve required data
    guild = session.query(Guild).filter(Guild.guild_id == giving_user.guild.id).first()
    giving_user = next((x for x in guild.users if int(x.user_id) == int(giving_user.id)), None)
    receiving_user = next((x for x in guild.users if int(x.user_id) == int(receiving_user.id)), None)

    # Check if pre-existing matching karma event
    event_check = session.query(KarmaEvents).filter((KarmaEvents.user_giving_id == giving_user.id) &
                                                    (KarmaEvents.user_receiving_id == receiving_user.id)).first()
    check = ""
    if event_check:
        # The event already exists, check datetimes!
        if event_check.datetime != datetime.today().date():
            event_check.datetime = datetime.today().date()
            check = True
        else:
            check = False
    else:
        # The event doesn't exist, make a new one!
        session.add(KarmaEvents(giving_user.id, receiving_user.id, datetime.today().date()))
        check = True

    session.commit()
    session.close()
    return check


def retrieve_user(user):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == user.guild.id).first()
    user = next((x for x in guild.users if int(x.user_id) == int(user.id)), None)
    dbuser = AttrDict()
    dbuser.update({"name" : user.name, "user_id" : user.user_id, "messages_sent" : user.messages_sent,
                   "activity_points" : user.activity_points, "karma" : user.karma, "last_message" : user.last_message})
    session.commit()
    session.close()
    return dbuser


def check_user_last_message(user):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == user.guild.id).first()
    user = next((x for x in guild.users if int(x.user_id) == int(user.id)), None)
    if user.last_message is None:
        user.last_message = datetime.now()
    if services.difference_in_minutes(user.last_message, datetime.now()) > 1:
        user.last_message = datetime.now()
        result = True
    else:
        result = False
    session.commit()
    session.close()
    return result


def check_reaction(emoji_id, guild_id):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild_id).first()

    if guild.karma_emoji == emoji_id:
        return True
    else:
        return False


def add_role(guild_id, role, point_req, karma_req):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild_id).first()
    # Check if role already exists for guild
    if sum(str(x.role_id) == str(role.id) for x in guild.roles) is 0:
        # Add new role
        new_role = Role(role.id, point_req, karma_req)
        guild.roles.append(new_role)
        session.add(new_role)

    session.commit()
    session.close()


# Grab all role objects belonging to guild and return them as a list
def retrieve_roles(guild_id):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild_id).first()
    roles = guild.roles
    return roles
    session.close()


# Remove role for guild
def remove_role(guild_id, role):
    session = Session()
    guild = session.query(Guild).filter(Guild.guild_id == guild_id).first()
    # Fetch role through guild
    role_to_remove = next((x for x in guild.roles if int(x.role_id) == int(role.id)), None)
    if role_to_remove is not None:
        guild.roles.remove(role_to_remove)
        session.delete(role_to_remove)
    session.commit()
    session.close()