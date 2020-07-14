#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
Sistemas Distribuidos
Curso 2019/2020
Práctica convocatoria extraordinaria
"""

import sys
import os
import binascii
import Ice

Ice.loadSlice("trawlnet.ice")
import TrawlNet

APP_DIRECTORY = "../"
FILES_DIRECTORY = os.path.join(APP_DIRECTORY, "files")


class SenderI(TrawlNet.Sender):
    """ Implementacion de la clase SenderI que hereda de TrawlNer.Sender"""

    def __init__(self, file_path):
        self.file_sender = open(file_path, "rb")

    def receive(self, size, current=None):
        """Manda un chunck del fichero del tamaño indicado"""
        return str(binascii.b2a_base64(self.file_sender.read(size), newline=False))

    def close(self, current=None):
        """ Cierra el fichero """
        self.file_sender.close()
        print("Sender closed!!")

    def destroy(self, current=None):
        """ Eliminará al sender del adaptador y terminará su ejecución """
        try:
            print("Sender destroyed!!")
            current.adapter.remove(current.id)
        except Exception as err:
            print("Error. {}".format(err))


class SenderFactoryI(TrawlNet.SenderFactory):
    """Implementacion de la clase SenderFactoryI que hereda de TrawlNet.SenderFactory"""

    def create(self, file_name, current=None):
        """Devolvera un objeto sender al que se le ha asignado el fichero fileName si existe"""
        try:
            file_path = os.path.join(FILES_DIRECTORY, file_name)
            servant = SenderI(file_path)
            proxy = current.adapter.addWithUUID(servant)
            print("# New sender for {} #".format(file_path))

        except Exception as err:
            print("Error. Sender failed {}".format(err))
            raise TrawlNet.FileDoesNotExistError(str(err))

        return TrawlNet.SenderPrx.checkedCast(proxy)


class SenderFactoryServer(Ice.Application):
    """Implementacion clase SenderFactoryServer que hereda de Ice.Application"""

    def run(self, argv):
        """Definicion del metodo run"""

        broker = self.communicator()

        adapter = broker.createObjectAdapter("SenderAdapter")
        servant = SenderFactoryI()
        proxy_sender_factory = adapter.add(
            servant, broker.stringToIdentity("senderFactory")
        )
        print("Sender Factory: {}".format(proxy_sender_factory), flush=True)

        # Start
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


if __name__ == "__main__":
    sender_factory = SenderFactoryServer()
    sys.exit(sender_factory.main(sys.argv))
