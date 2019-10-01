import discord, datetime, asyncio

#Discord setup
client = discord.Client()

@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client.user))
    await client.change_presence(activity=discord.Game(name="Mother 3"))

    global active_side_games, active_featured_games, \
           side_games_archive, side_games_archive_2, side_games_archive_3, \
           featured_games_archive, featured_games_archive_2, \
           featured_games_archive_3, moderator

    rpg_club = [x for x in client.guilds if str(x) == "The RPG Club"][0]
    active_side_games = [cat for cat in rpg_club.categories \
                          if str(cat) == "Active Side Games"][0]
    active_featured_games = [cat for cat in rpg_club.categories \
                          if str(cat) == "Active Featured Games"][0]
    side_games_archive = [cat for cat in rpg_club.categories \
                          if str(cat) == "Side Games Archive"][0]
    side_games_archive_2 = [cat for cat in rpg_club.categories \
                          if str(cat) == "Side Games Archive II"][0]
    side_games_archive_3 = [cat for cat in rpg_club.categories \
                          if str(cat) == "Side Games Archive III"][0]
    featured_games_archive = [cat for cat in rpg_club.categories \
                          if str(cat) == "Featured Games Archive"][0]
    featured_games_archive_2 = [cat for cat in rpg_club.categories \
                          if str(cat) == "Featured Games Archive II"][0]
    featured_games_archive_3 = [cat for cat in rpg_club.categories \
                          if str(cat) == "Featured Games Archive III"][0]
    moderator = [r for r in rpg_club.roles if str(r) == "moderators"][0]

@client.event
async def on_message(message):
    #Move archived game to active sgame if last 10 messages are < 1wk old on_msg
    if message.channel in side_games_archive.channels \
                        + side_games_archive_2.channels \
                        + side_games_archive_3.channels \
                        + featured_games_archive.channels \
                        + featured_games_archive_2.channels \
                        + featured_games_archive_3.channels:

        #assume revived at default for later variable check
        revived = True

        today = datetime.datetime.today()
        async for msg in message.channel.history(limit=10):
            if ((today - msg.created_at) > datetime.timedelta(days=7)):
                revived = False
                break

        if revived:
            await message.channel.edit(category=active_side_games)

            sorted_actives = sorted(active_side_games.channels,
                                    key=lambda s_g: str(s_g))

            for s_g in sorted_actives[::-1]:
                await s_g.edit(position=0)

    #Mod command to update now playing of the bot
    if message.content.startswith('!np '):
        if moderator in message.author.roles:
            await client.change_presence(activity = \
                                         discord.Game(name=message.content[4:]))

async def move_retired_sidegames(): #revived featured games count as sidegames
    while not client.is_closed():
        try:
            retired_sidegames = {"side": [], "featured": []}
            moving = {"side": False, "featured": False}

            for asg in active_side_games.channels:
                async for msg in asg.history(limit=1):
                    today = datetime.datetime.today()
                    if ((today - msg.created_at) > datetime.timedelta(days=7)):
                        if "_r" in str(asg):
                            try:
                                after_r = str(asg).index("_r")+2
                                int(str(asg)[after_r])
                                moving["featured"] = True
                                retired_sidegames["featured"].append(asg)
                            except ValueError:
                                #you get here if _r is just part of the title
                                #and there isn't actually a round no. after it
                                moving["side"] = True
                                retired_sidegames["side"].append(asg)
                        else:
                            moving["side"] = True
                            retired_sidegames["side"].append(asg)

            for i in range(2):
                #on different runs of the loop
                #check each moving value independently
                #and move if necessary
                if i==0 and moving["side"]:
                    archive = side_games_archive
                    archive_2 = side_games_archive_2
                    archive_3 = side_games_archive_3
                    s_or_f = "side"
                elif i==1 and moving["featured"]:
                    archive = featured_games_archive
                    archive_2 = featured_games_archive_2
                    archive_3 = featured_games_archive_3
                    s_or_f = "featured"
                else:
                    continue

                all_archived = [chn for chn in archive.channels]     \
                               + [chn for chn in archive_2.channels]   \
                               + [chn for chn in archive_3.channels]   \
                               + retired_sidegames[s_or_f]

                all_archived = sorted(all_archived,
                                        key=lambda s_g: str(s_g))

                for s_g in all_archived:
                    #position is to force ascend positioning on the channels
                    #otherwise whatever old one is there is silently maintained
                    await s_g.edit(category=None, position=173)

                count=1
                for s_g in all_archived:
                    if count < 51:
                        await s_g.edit(category=archive)
                    elif count < 101:
                        await s_g.edit(category=archive_2)
                    else:
                        await s_g.edit(category=archive_3)
                    count+=1
            await asyncio.sleep(604800) #1 week in seconds
        except:
            #for some reason, create_task functions outrace the bot running
            #even when using client.wait_until_ready()
            #so need to use this to cool the otherwise terminating exceptions
            #thereby giving the bot time to actually get running
            #and then the async loop can actually exist afterwards
            await asyncio.sleep(60)

async def move_old_gotm():
    while not client.is_closed():
        try:
            if datetime.datetime.today().day == 1:
                retired_games = []
                for afg in active_featured_games.channels:
                    if "_r" in str(afg):
                        retired_games.append(afg)
                if len(retired_games)==4:
                    #if the new gotm is already there,
                    #sort the channels so that only the old ones get removed
                    retired_games = sorted(retired_games,
                                           key=lambda c: str(c)[-2:])[0:2]

                    for r_g in retired_games:
                        await r_g.edit(category=active_side_games)

                    sorted_actives = sorted(active_side_games.channels,
                                            key=lambda s_g: str(s_g))

                    for s_g in sorted_actives[::-1]:
                        await s_g.edit(position=0)

            await asyncio.sleep(86400) #check every 24 hours
        except:
            await asyncio.sleep(60)

client.loop.create_task(move_retired_sidegames())
client.loop.create_task(move_old_gotm())

client.run('token_goes_here')
