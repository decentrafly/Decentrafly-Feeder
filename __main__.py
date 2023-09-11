import config
import check_version
import logging
import sys

config.basic_logging()
log = logging.getLogger("__main__")
log.debug("Entry point")


def help():
    print("Specify a command: (adsb-forwarder|agent|enable|install|mlat-forwarder|requirements|sender|setup|upgrade|version)")


def main():
    args = sys.argv
    log.debug("Command line arguments: %s", args)
    if len(args) < 2:
        help()
        exit(1)
    executable = args[0]
    command = args[1]

    log.debug("Checking if we are running a sufficiently new python")
    check_version.check()

    log.debug("Import commands code")
    import adsb_forwarder
    import agent
    import device_setup
    import mlat_forwarder
    import sender
    import zipfile

    log.debug("Dispatch")
    if command == "adsb-forwarder":
        adsb_forwarder.run()
    elif command == "agent":
        agent.run()
    elif command == "enable":
        device_setup.enable_services(executable)
    elif command == "install":
        device_setup.install(executable)
    elif command == "install-agent":
        device_setup.install_agent()
    elif command == "mlat-forwarder":
        mlat_forwarder.run()
    elif command == "requirements":
        with zipfile.ZipFile(executable) as z:
            with z.open('requirements.txt') as zf:
                print(zf.read().decode("utf-8"))
    elif command == "sender":
        sender.run()
    elif command == "setup":
        device_setup.self_setup()
        device_setup.update_iot_device()
    elif command == "setup-agent":
        device_setup.setup_agent()
    elif command == "update-config":
        device_setup.update_config()
    elif command == "upgrade":
        device_setup.upgrade(executable)
        device_setup.update_config()
    elif command == 'version':
        with zipfile.ZipFile(executable) as z:
            with z.open('version.txt') as zf:
                print(zf.read().decode("utf-8").strip())

    log.debug("Terminating")


if __name__ == '__main__':
    main()
