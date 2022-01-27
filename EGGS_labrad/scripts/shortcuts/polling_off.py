# connect to utils
import labrad
cxn = labrad.connect()


# try to turn polling off for each server
for server in cxn.servers.values():
    try:
        server.polling(False)
    except Exception as e:
        print(e)