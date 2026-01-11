from mode import Service


class Thumbnail(Service):
    
    @Service.task
    async def _my_coro(self) -> None:
        print('Executing coroutine')

