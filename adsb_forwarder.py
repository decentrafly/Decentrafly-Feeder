from config import ec
import asyncio
import logging
import ssl


logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
logger.info("Logger initialized")


def ssl_context():
    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH,
                                         cafile=ec('DCF_CA_FILE'))
    context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
    context.check_hostname = True
    context.load_cert_chain(ec('DCF_CLIENT_CRT_FILE'),
                            keyfile=ec('DCF_CLIENT_KEY_FILE'))
    return context


async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            writer.write(await reader.read(4096))
    finally:
        writer.close()


async def start_forwarder():
    context = ssl_context()
    logger.info("Connecting ...")
    forwarding_connection_future = asyncio.open_connection(
        host=ec('DCF_SECURE_ADSB_HOST'),
        port=int(ec('DCF_SECURE_ADSB_PORT')),
        server_hostname=ec('DCF_SECURE_ADSB_HOSTNAME'),
        ssl=context
    )
    reading_connection_future = asyncio.open_connection(
        ec('DCF_READSB_HOST'),
        int(ec('DCF_READSB_PORT'))
    )

    try:
        remote_reader, remote_writer = await forwarding_connection_future
    except Exception as e:
        logger.error("Failed to connect to secure remote")
        logger.error(e)
        exit(2)

    try:
        local_reader, local_writer = await reading_connection_future
    except Exception:
        logger.error("Failed to connect to readsb")
        exit(2)

    fw = pipe(local_reader, remote_writer)
    bw = pipe(remote_reader, local_writer)

    try:
        logger.info("Forwarding!")
        await asyncio.gather(fw, bw)
    except Exception:
        logger.error("Connection failed")
    finally:
        logger.info("Closing connection")

    logger.info("Exiting")


def run():
    asyncio.run(start_forwarder())
