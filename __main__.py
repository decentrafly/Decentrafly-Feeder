import config
import check_version
import logging
import sys

config.basic_logging()
log = logging.getLogger("__main__")
log.debug("Entry point")


def help():
    print("""Specify a command:
    adsb-forwarder:      Connect to ADSB out and securely forward data to decentrafly
    agent                The agent updates device info and optionally allows remote access (turned off by default)
    enable               Makes sure all services are running
    install              Install this binary to /usr/bin
    install-localproxy   Needed for remote access. Only downloads tool, does not enable remote access.
    mlat-forwarder       Securely forwards mlat-client output to decentrafly
    requirements         Shows contents of the requirements.txt used to build this Python code.
    sender               Deprecated MQTT forwarder.
    setup                Installs certificates and registers this device with the decentrafly backend.
    setup-remote-access  Enables remote access. This allows decentrafly staff to ssh into your device. (Can be disabled in /etc/decentrafly/config.json)
    update-config        Update the dynamic parts of the config, such as decentrafly endpoints.
    upgrade              Pull the latest decentrafly version and replace it.
    version              Show version and exit.""")


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
    elif command == "install-localproxy":
        device_setup.install_localproxy()
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
        device_setup.update_config()
    elif command == "setup-remote-access":
        device_setup.setup_remote_access()
    elif command == "update-config":
        device_setup.update_config()
    elif command == "upgrade":
        device_setup.upgrade(executable)
        device_setup.update_config()
        device_setup.enable_services(executable)
    elif command == "version":
        with zipfile.ZipFile(executable) as z:
            with z.open('version.txt') as zf:
                print(zf.read().decode("utf-8").strip())
    else:
        help()

    log.debug("Terminating")


if __name__ == '__main__':
    main()
