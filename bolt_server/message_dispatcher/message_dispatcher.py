'''
File: message_dispatcher.py
Description: Message dispatch handler
Date: 29/09/2017
Author: Saurabh Badhwar <sbadhwar@redhat.com>
'''
from structures import Message, MessagePacket, MessageQueue

class MessageDispatcher(object):
    """Handle the dispatch of the message from the bolt server

    Registers new messages for the dispatch handling based on the subscribed
    topics.
    """

    def __init__(self, socket_server):
        """Initialize the MessageDispatcher

        Keyword Arguments:
        socket_server -- A socket server object to help with the message dispatch
        """

        #The general purpose message register looks like
        # message_register = {message_name: [topics]}
        self.message_register = {}

        #Socket server
        self.socket_server = socket_server

        #Message structure store
        self.message_store = Message()

        #Initialize the Message Queue
        self.message_queue = MessageQueue()

        #Register a message handler with Socket server
        self.socket_server.register_handler(self.__generic_handler)

    def message_exists(self, message_name):
        """Check if the message exists or not

        Keyword arguments:
        message_name -- The name of the message

        Returns:
            Bool
        """

        try:
            self.message_store.get_message(message_name)
        except KeyError:
            return False

        return True

    def register_handler(self, handler):
        """Register a new message handler with the socket server

        Keyword arguments:
        handler -- Message handling object
        """

        self.socket_server.register_handler(handler)

    def register_message(self, message_name, message_structure, message_topics):
        """Register a new message

        Keyword arguments:
        message_name -- The name of the message
        message_strcuture -- The name of the structure
        message_topics -- The topics to which the message should be broadcasted

        Returns: Bool
        """

        try:
            self.message_store.add_message(message_name, message_structure)
        except RuntimeError:
            return False

        self.message_register[message_name] = message_topics
        return True

    def unregister_message(self, message_name):
        """Unregister a provided message

        Keyword arguments:
        message_name -- The name of the message to be removed
        """

        if message_name in self.message_register.keys():
            self.message_store.remove_message(message_name)
            del self.message_register[message_name]

    def send_message(self, message_name, params={}):
        """Send a new message

        Keyword arguments:
        message_name -- The name of the message to be sent
        params -- The parameters to be added to the message

        Raises:
            KeyError if the params provided do not match message structure
            RuntimeError if the message sending fails

        Returns:
            Integer
        """

        message_structure = self.__get_message_structure(message_name)
        for key in params.keys():
            if key not in message_structure.keys():
                raise KeyError("Parameter mismatch in message structure and provided params")
            else:
                message_structure[key] = params[key]

        message_packet = MessagePacket(message_structure)
        try:
            for topic in self.message_register[message_name]:
                mid, packet = message_packet.get_packet()
                self.socket_server.send_message(topic, packet)
                self.message_queue.queue(mid)
            return mid
        except RuntimeError:
            raise RuntimeError("Unable to send the message across the topics")
            pass

    def __get_message_structure(self, message_name):
        """Get the message structure

        Keyword arguments:
        message_name -- The name of the message whose structure needs to be
                        retrieved

        Returns:
            Mixed The message structure
        """

        return self.message_store.get_message(message_name)

    def __generic_handler(self, message):
        """Generic message handler

        Handles the incoming messages on a generic basis by printing them and
        marking the message as completed.

        Keyword arguments:
        message -- The incoming message object
        """

        mid = message['id']
        result = message['result']
        self.message_queue.update_status(mid, 'Completed')
