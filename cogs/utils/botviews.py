import discord


class X(discord.ui.View):
    """Simple class to offer a delete button"""

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="", emoji="\U0001f5d1")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.user.id:
            return await interaction.response.send_message("No.", ephemeral=True)
        self.stop()
        await interaction.message.delete()


class Confirm(discord.ui.View):
    def __init__(self, disable_after_click: bool = False):
        super().__init__()
        self.value = None
        self.do_disable = disable_after_click

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != interaction.user.id:
            return await interaction.response.send_message("No.", ephemeral=True)
        if self.do_disable:
            for c in self.children:
                c.disabled = True
            await interaction.response.edit_message(
                content=interaction.message.content, view=self
            )
        else:
            await interaction.response.defer()
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.user.id:
            return await interaction.response.send_message("No.", ephemeral=True)
        if self.do_disable:
            for c in self.children:
                c.disabled = True
            await interaction.response.edit_message(
                content=interaction.message.content, view=self
            )
        else:
            await interaction.response.defer()
        self.value = False
        self.stop()
