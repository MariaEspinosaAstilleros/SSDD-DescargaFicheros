#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
Sistemas Distribuidos
Curso 2019/2020
Práctica convocatoria extraordinaria
"""

import sys
import argparse
import Ice
import utils

Ice.loadSlice("trawlnet.ice")
import TrawlNet


class TransferI(TrawlNet.Transfer):
    """ Implementacion de la clase TransferI que hereda de TrawlNer.Transfer"""

    def __init__(self, receiver_factory, sender_factory, transfer_event):
        self.receiver_factory = receiver_factory
        self.sender_factory = sender_factory
        self.transfer_event = transfer_event
        self.proxy = None
        self.transfer = None
        self.dict_peers = {}

    def createPeers(self, files, current=None):
        """Crea una pareja receiver-sender por cada fichero que se desea transferir"""
        try:
            receiver_list = list()
            self.transfer = TrawlNet.TransferPrx.checkedCast(self.proxy)

            for i in files:
                sender = self.sender_factory.create(i)
                receiver = self.receiver_factory.create(i, sender, self.transfer)
                self.dict_peers["../files/" + i] = [sender, receiver]
                receiver_list.append(receiver)

        except Exception as err:
            print("Error. Transfer create peers failed {}".format(err))
            raise TrawlNet.FileDoesNotExistError(str(err))

        return receiver_list

    def destroyPeer(self, peer_id, current=None):
        """Destruye la pareja receiver-sender que se corresponde con un id dado"""
        self.dict_peers[peer_id][0].destroy()
        self.dict_peers[peer_id][1].destroy()
        self.dict_peers.pop(peer_id)
        print("Peer of {} destroyed!!".format(peer_id))

        if len(self.dict_peers) == 0:
            self.transfer_event.transferFinished(self.transfer)

    def destroy(self, current=None):
        """ Eliminará al transfer del adaptador y terminará su ejecución"""
        print("Transfer destroyed!!")
        current.adapter.remove(current.id)


class TransferFactoryI(TrawlNet.TransferFactory):
    """ Implementacion de la clase TransferFactoryI que hereda de TrawlNet.TransferFactory"""

    def __init__(self, sender_factory, broker, transfer_event):
        self.sender_factory = sender_factory
        self.broker = broker
        self.transfer_event = transfer_event

    def newTransfer(self, receiver_factory, current=None):
        """Devuelve un objeto transfer. Necesita receiverFactory para
        la creacion de receivers en el lado del cliente"""
        servant = TransferI(receiver_factory, self.sender_factory, self.transfer_event)
        proxy = current.adapter.add(servant, self.broker.stringToIdentity("transfer"))
        servant.proxy = proxy
        print("# New transfer for {} #".format(proxy))

        return TrawlNet.TransferPrx.checkedCast(proxy)


class PeerEventI(TrawlNet.PeerEvent):
    """Implementacion de la clase PeerEventI que hereda de TrawlNet.PeerEvent"""

    def peerFinished(self, peer_info, current=None):
        """Notifica a todos los transfers que el fichero está listo"""
        peer_id = "../files/" + peer_info.fileName
        peer_transfer = peer_info.transfer
        peer_transfer.destroyPeer(peer_id)


class TransferManagerServer(Ice.Application):
    """Implementacion clase TransferManagerServer que hereda de Ice.Application"""

    transfer_event = None

    def run(self, argv):
        """Definicion del metodo run"""

        broker = self.communicator()
        args = self.arguments()

        # Proxy del evento
        servant_peer_event = PeerEventI()
        adapter_event = broker.createObjectAdapter("PeerEventAdapter")
        subscriber = adapter_event.addWithUUID(servant_peer_event)

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
        utils.create_subscriber(subscriber, peer_topic)

        # Publisher
        transfer_event = utils.create_publisher(transfer_topic, topic_transfer_event)

        # Proxy del sender factory
        proxy = broker.stringToProxy(args.sender_factory)
        sender_factory = TrawlNet.SenderFactoryPrx.checkedCast(proxy)

        # Proxy del transfer factory
        adapter = broker.createObjectAdapter("TransferAdapter")
        servant = TransferFactoryI(sender_factory, broker, transfer_event)
        proxy_transfer_factory = adapter.add(
            servant, broker.stringToIdentity("transferFactory")
        )
        print("Transfer Factory: {}".format(proxy_transfer_factory), flush=True)

        adapter_event.activate()
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

    def arguments(self):
        """Indica los argumentos de linea de comandos que necesita el transfer"""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-s", "--sender_factory", required=True, help="Proxy of sender factory"
        )

        args = parser.parse_args()
        return args


if __name__ == "__main__":
    transfer_manager = TransferManagerServer()
    sys.exit(transfer_manager.main(sys.argv))
