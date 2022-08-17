from netinstall import Flasher

flash = Flasher()
while True:
    try:
        flash.run()
    except KeyboardInterrupt:
        print("Stopping the Flasher")
        break
    except:
        pass
    