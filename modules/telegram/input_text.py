from modules.core.base_block import BaseBlock


class TextInputBlock(BaseBlock):
    id = "telegram.input"
    name = "Receive Message"
    category = "telegram"

    def compile(self, context):
        return """
@router.message()
async def receive(message):
    text = message.text

"""