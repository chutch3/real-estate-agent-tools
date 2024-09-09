class PostGenerationService:
    async def generate_post(self, address, agent_info, custom_template):
        raise NotImplementedError("This method must be implemented by a subclass")
