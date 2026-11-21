from modules.core.base_block import BaseBlock


class SendMessageBlock(BaseBlock):
    id = "telegram.send_message"
    name = "Send Message"
    category = "telegram"

    def compile(self, context):
        text = context.get("text", "")
        return f"""
await bot.send_message(
    chat_id,
    {text!r}
)

"""

    def imports(self):
        return []
