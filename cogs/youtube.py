import discord
from discord.ext import commands, tasks
import os
import json

class Youtube(commands.Cog, name='youtube'):
    def __init__(self, bot) -> None:
        self.bot = bot