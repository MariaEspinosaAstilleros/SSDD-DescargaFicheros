#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sistemas Distribuidos
Curso 2019/2020
Práctica convocatoria extraordinaria
"""

import Ice
import IceStorm

Ice.loadSlice("trawlnet.ice")
import TrawlNet


def get_topic(broker):
    """Obtenemos el topic para el canal de eventos"""
    key = "IceStorm.TopicManager.Proxy"
    proxy = broker.propertyToProxy(key)
    if proxy is None:
        print("Property '{}' not set".format(key))
        return None

    return IceStorm.TopicManagerPrx.checkedCast(proxy)


def retieve_topic(topic, topic_name):
    """Recuperamos el topic. Si no existe lo creamos"""
    try:
        topic_event = topic.retrieve(topic_name)
    except IceStorm.NoSuchTopic:
        print("No such topic found, creating")
        topic_event = topic.create(topic_name)

    return topic_event


def create_publisher(topic_event, topic_name):
    """ Se crea el publicador dependiendo del nombre del topic"""
    publisher = topic_event.getPublisher()
    if topic_name == "PeerEventSync":
        return TrawlNet.PeerEventPrx.uncheckedCast(publisher)
    if topic_name == "TransferEventSync":
        return TrawlNet.TransferEventPrx.uncheckedCast(publisher)


def create_subscriber(subscriber, topic_event):
    """Se crea el subscriptor dependiendo del evento"""
    qos = {}
    topic_event.subscribeAndGetPublisher(qos, subscriber)
    print("Waiting events... '{}'".format(subscriber))
