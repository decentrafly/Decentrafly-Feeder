import check_version
import device_setup
import mlat_forwarder
import sender
import sys
import zipfile


def help():
    print("Specify a command: (setup|sender|enable)")


def main():
    args = sys.argv
    if len(args) < 2:
        help()
        exit(1)
    executable = args[0]
    command = args[1]

    check_version.check()

    if command == "enable":
        device_setup.enable_services(executable)
    elif command == "install":
        device_setup.install(executable)
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
    elif command == 'version':
        with zipfile.ZipFile(executable) as z:
            with z.open('version.txt') as zf:
                print(zf.read().decode("utf-8").strip())


if __name__ == '__main__':
    main()
