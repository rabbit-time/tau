import discord
from discord.ext import commands

import perms

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def pre(self, ctx, msg):
        await ctx.message.delete()
        
        if msg.author != ctx.guild.me:
            return await ctx.send(f'{ctx.author.mention} Sorry, I can only edit my own messages!', delete_after=5)

        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break

        if not isinstance(embed, discord.Embed): raise commands.BadArgument

        return embed

    @commands.command(cls=perms.Lock, name='embed', aliases=[], usage='embed')
    async def embed(self, ctx):
        '''Create a new embed.\n
        **Example:```yml\n.embed```**
        '''
        await ctx.send(embed=discord.Embed())

    @commands.command(cls=perms.Lock, name='setcontent', aliases=[], usage='setcontent <message> <text>')
    async def setcontent(self, ctx, msg: discord.Message, *, text):
        '''Modify the content of the message with the embed.\n
        **Example:```yml\n.setcontent 694890918645465138 Hi!```**
        '''
        embed = await self.pre(ctx, msg)

        await msg.edit(content=text, embed=embed)

    @commands.command(cls=perms.Lock, name='setdesc', aliases=[], usage='setdesc <message> <text>')
    async def setdesc(self, ctx, msg: discord.Message, *, text):
        '''Modify the description of an embed.\n
        **Example:```yml\n.setdesc 694890918645465138 Tau is the best!```**
        '''
        embed = await self.pre(ctx, msg)
        embed.description = text

        await msg.edit(embed=embed)

    @commands.command(cls=perms.Lock, name='setcolor', aliases=[], usage='setcolor <message> <color>')
    async def setcolor(self, ctx, msg: discord.Message, color: discord.Color):
        '''Modify the color of an embed.
        *color* must be in hexadecimal format.\n
        **Example:```yml\n.setcolor 694890918645465138 #8bb3f8```**
        '''
        embed = await self.pre(ctx, msg)
        embed.color = color

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='settitle', aliases=[], usage='settitle <message> <text>')
    async def settitle(self, ctx, msg: discord.Message, *, title=''):
        '''Modify the title of an embed.\n
        **Example:```yml\n.settitle 694890918645465138 Mistborn```**
        '''
        embed = await self.pre(ctx, msg)
        embed.title = title if len(title) <= 256 else title[:256]

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='setfooter', aliases=[], usage='setfooter <message> <text>')
    async def setfooter(self, ctx, msg: discord.Message, *, footer=''):
        '''Modify the footer text of an embed.\n
        **Example:```yml\n.setfooter 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.footer.icon_url != discord.Embed.Empty and not footer:
            footer = u'\u200b'
        
        embed.set_footer(text=footer, icon_url=embed.footer.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='setfootericon', aliases=[], usage='setfootericon <message> <url>')
    async def setfootericon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the footer icon of an embed.\n
        **Example:```yml\n.setfootericon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        text = embed.footer.text if embed.footer.text else u'\u200b'
        embed.set_footer(text=text, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='setauthor', aliases=[], usage='setauthor <message> <name>')
    async def setauthor(self, ctx, msg: discord.Message, *, name=''):
        '''Modify the author name of an embed.\n
        **Example:```yml\n.setauthor 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.author.icon_url != discord.Embed.Empty and not name:
            name = u'\u200b'
        
        embed.set_author(name=name, icon_url=embed.author.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='setauthoricon', aliases=[], usage='setauthoricon <message> <url>')
    async def setauthoricon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author icon of an embed.\n
        **Example:```yml\n.setauthoricon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        name = embed.author.name if embed.author.name else u'\u200b'
        embed.set_author(name=name, url=embed.author.url, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='setauthorurl', aliases=[], usage='setauthorurl <message> <url>')
    async def setauthorurl(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author URL of an embed.\n
        **Example:```yml\n.setauthorurl 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_author(name=embed.author.name, url=url, icon_url=embed.author.icon_url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='setimage', aliases=[], usage='setimage <message> <url>')
    async def setimage(self, ctx, msg: discord.Message, url=''):
        '''Modify the image of an embed.\n
        **Example:```yml\n.setimage 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_image(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='setthumbnail', aliases=[], usage='setthumbnail <message> <url>')
    async def setthumbnail(self, ctx, msg: discord.Message, url=''):
        '''Modify the thumbnail of an embed.\n
        **Example:```yml\n.setthumbnail 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_thumbnail(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
        
def setup(bot):
    bot.add_cog(Embed(bot))