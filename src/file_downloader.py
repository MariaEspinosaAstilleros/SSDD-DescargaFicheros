#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sistemas Distribuidos
Curso 2019/2020
Práctica convocatoria extraordinaria
"""

import sys
import os
import binascii
import argparse
import Ice
import utils

Ice.loadSlice("trawlnet.ice")
import TrawlNet

APP_DIRECTORY = "../"
DOWNLOADS_DIRECTORY = os.path.join(APP_DIRECTORY, "downloads")


class ReceiverI(TrawlNet.Receiver):
    """Implementacion de la clase ReceiverI que hereda de TrawlNet.Receiver"""

    def __init__(self, file_path, sender, transfer, file_name, peer_event):
        self.file_descriptor = open(file_path, "wb")
        self.sender = sender
        self.transfer = transfer
        self.file_name = file_name
        self.peer_event = peer_event

    def start(self, current=None):
        """Inicia la recepción del fichero"""
        chunck_size = 1024
        self.transferData(self.file_descriptor, self.sender, chunck_size)
        self.notifyTransferFinish(self.peer_event)

    def destroy(self, current=None):
        """Elimina el transfer de su adaptador y termina su ejecución"""
        print("Receiver destroyed!!")
        current.adapter.remove(current.id)

    def transferData(self, file_descriptor, sender, chunck_size):
        """Recorre el fichero que solicita el cliente para transferirlo """
        remote_eof = False
        with file_descriptor:
            remote_eof = False
            while not remote_eof:
                data = sender.receive(chunck_size)
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remote_eof = len(data) < chunck_size
                if data:
                    file_descriptor.write(data)
            sender.close()

        print("The data transfer has been finished!")

    def getPeerInfo(self, transfer, file_name):
        """Obtenemos el objeto PeerInfo"""
        peer_info = TrawlNet.PeerInfo()
        peer_info.transfer = transfer
        peer_info.fileName = file_name

        return peer_info

    def notifyTransferFinish(self, peer_event):
        """Se emite el evento cuando ha terminado la transferencia """
        peer_info = self.getPeerInfo(self.transfer, self.file_name)
        peer_event.peerFinished(peer_info)


class ReceiverFactoryI(TrawlNet.ReceiverFactory):
    """Implementacion de la clase ReceiverFactoryI que hereda de TrawlNet.ReceiverFactory"""

    def __init__(self, peer_event):
        self.peer_event = peer_event

    def create(self, file_name, sender, transfer, current=None):
        """Devuelve un objeto receiver al que se le ha asignado un compañero sender
        y un fichero fileName. Se indica el transfer que lo creó para que pueda ser
        notificado al terminar"""

        file_path = os.path.join(DOWNLOADS_DIRECTORY, file_name)
        servant = ReceiverI(file_path, sender, transfer, file_name, self.peer_event)
        proxy = current.adapter.addWithUUID(servant)
        print("# New receiver for {} #".format(file_path))

        return TrawlNet.ReceiverPrx.checkedCast(proxy)


class TransferEventI(TrawlNet.TransferEvent):
    """Implementacion de la clase TransferEventI que hereda de TrawlNer.TransferEvent"""

    def __init__(self, broker):
        self.broker = broker

    def transferFinished(self, transfer, current=None):
        """Notifica a todos los clientes que la transferencia del objeto transfer ha finalizado"""
        transfer.destroy()
        self.broker.shutdown()


class FileDownloader(Ice.Application):
    """Implementacion clase FileDownloader que hereda de Ice.Application"""

    def run(self, args):
        """Definicion del metodo run"""

        broker = self.communicator()
        args = self.arguments()

        # Proxy del evento
        servant_transfer_event = TransferEventI(broker)
        adapter_event = broker.createObjectAdapter("TransferEventAdapter")
        adapter_event.activate()
        subscriber = adapter_event.addWithUUID(servant_transfer_event)

        # Object for event channel
        topic = utils.get_topic(broker)
        if not topic:
            raise ValueError("Proxy is not IceStorm")

        ## Canales de eventos
        topic_peer_event = "PeerEventSync"
        topic_transfer_event = "TransferEventSync"

        peer_topic = utils.retieve_topic(topic, topic_peer_event)
        transfer_topic = utils.retieve_topic(topic, topic_transfer_event)

        # Subscriber
        utils.create_subscriber(subscriber, transfer_topic)

        # Publisher
        peer_event = utils.create_publisher(peer_topic, topic_peer_event)

        # Proxy del transfer factory
        proxy = broker.stringToProxy(args.transfer_factory)
        transfer_factory = TrawlNet.TransferFactoryPrx.checkedCast(proxy)

        ## Creamos el proxy del receiver factory
        adapter = broker.createObjectAdapter("ReceiverAdapter")
        adapter.activate()
        servant = ReceiverFactoryI(peer_event)
        proxy_receiver_factory = adapter.add(
            servant, broker.stringToIdentity("receiverFactory")
        )
        receiver_factory = TrawlNet.ReceiverFactoryPrx.checkedCast(
            proxy_receiver_factory
        )

        self.startDataTransfer(broker, args, transfer_factory, receiver_factory)

        broker.waitForShutdown()

        return 0

    def arguments(self):
        """Indica los argumentos de linea de comandos que necesita el cliente"""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-t", "--transfer_factory", required=True, help="Proxy of transfer factory"
        )
        parser.add_argument(
            "-f",
            "--files",
            action="append",
            required=True,
            dest="file_list",
            default=[],
            help="Add file name to a file_list",
        )

        args = parser.parse_args()
        return args

    def startDataTransfer(self, broker, args, transfer_factory, receiver_factory):
        """Comprueba si los ficheros solicitados existen. Si alguno no existe la
        transferencia se da por fallida. Si todos los ficheros existen comienza
        la transferencia de los ficheros"""
        path = "../files/"
        dirs = os.listdir(path)
        cont = 0

        for file_name in args.file_list:
            if file_name in dirs:
                cont += 1
                if cont == len(args.file_list):
                    transfer = transfer_factory.newTransfer(receiver_factory)
                    receivers = transfer.createPeers(args.file_list)
                    for i in receivers:
                        i.start()
            else:
                print("The data transfer has been failed. The file '{}' does not exist in the directory {}".format(file_name, path))
                broker.shutdown()


if __name__ == "__main__":
    file_downloader = FileDownloader()
    sys.exit(file_downloader.main(sys.argv))