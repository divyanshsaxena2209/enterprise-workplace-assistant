import asyncio
import socket

if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
    del socket.SO_EXCLUSIVEADDRUSE

async def main():
    server = await asyncio.start_server(lambda r, w: None, '127.0.0.1', 8080)
    print('OK')
    server.close()
    await server.wait_closed()
asyncio.run(main())
