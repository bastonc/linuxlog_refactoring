import asyncio
import websockets

async def reciever():

    uri = "ws://localhost:40001"
    async with websockets.connect(uri) as websocket:
        #await websocket.send("Hello world!")
        async for message in websocket:
             print(message)
            #string = await websocket.recv()
            #print(message)


async def handler():
    consumer_task = asyncio.create_task(reciever())
     #asyncio.get_event_loop().run_until_complete(reciever())

    done, pending = await asyncio.wait(
        [consumer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

#asyncio.get_event_loop().run_until_complete(hello())