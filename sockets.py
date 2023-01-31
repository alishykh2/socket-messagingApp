import json
import uuid
import datetime
import socket
from threading import Thread
import time

isListening = True


class MessageBoard:
    def __init__(self, author):
        data = self.readJsonFile("data.json")
        self.messages = data["messages"] if "messages" in data else []
        self.peers = []
        self.author = author
        self.stop_threads = False
        while True:
            try:
                port = input("Enter a port: ")
                if not port:
                    print("Enter valid port")
                    continue
                s = socket.socket()
                self.socket = s
                print("Socket successfully created")
                s.bind(("localhost", int(port)))
                print("socket binded to %s" % (port))
                s.listen(5)
                print("socket is listening")
                break
            except socket.error as e:
                print(e)

    def readJsonFile(self, filename):
        try:
            file = open("data.json")
            return json.load(file)
        except Exception as e:
            print("Can't load data from %s" % filename)

    def listenPeers(self):
        try:
            while True:
                if self.stop_threads:
                    break
                c, addr = self.socket.accept()
                option = c.recv(1024).decode()
                if option == "sync peers":
                    c.send(
                        json.dumps(
                            self.peers,
                        ).encode()
                    )
                if option == "sync message":
                    c.send(
                        json.dumps(
                            self.messages,
                        ).encode()
                    )
                c.close()
        except Exception as e:
            print(f"Something went wrong: {e}")

    def connect(self, port):
        if port:
            try:
                cSocket = socket.socket()
                cSocket.connect(("localhost", int(port)))
                self.peers.append(int(port))
                cSocket.close()
            except socket.error as e:
                print(f"Error connecting to peer: {e}")

    def add_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_id = str(uuid.uuid4())
        new_message = {
            "id": message_id,
            "timestamp": timestamp,
            "message": message,
            "author": self.author,
        }
        self.messages.append(new_message)
        self.printMessages()
        self.dumpDataToFile()
        return message_id

    def printMessages(self):
        for message in self.messages:
            print("id ---- ", message["id"])
            print("timestamp ---- ", message["timestamp"])
            print("message ---- ", message["message"])
            print("author ---- ", message["author"])
            print("****************************************************************")
            print()

    def connect_peer(self):
        try:
            self.printPeers()
            peer_port = int(input("Enter peer port: "))
            if peer_port in self.peers:
                print("Already connected to peer")
            else:
                self.connect(peer_port)
                self.dumpDataToFile()
        except socket.error as e:
            print(f"Error connecting to peer: {e}")

    def printPeers(self):
        for peer in self.peers:
            print("peer ---- ", peer)

        print("--------------------------------\n")

    def syncAfterInterval(self, interval):
        while True:
            if self.stop_threads:
                break
            self.sync_messages(),
            self.sync_peers(),
            time.sleep(interval)

    def sync_messages(self):
        for peer in self.peers:
            try:
                s = socket.socket()
                s.connect(("", int(peer)))
                message_data = ("sync message").encode()
                s.send(message_data)

                peer_messages = json.loads(s.recv(1024).decode())
                for message in peer_messages:
                    existing_message = next(
                        (m for m in self.messages if m["id"] == message["id"]), None
                    )
                    if existing_message is None:
                        self.messages.append(message)
                    else:
                        existing_message.update(message)
                s.close()
                self.messages = sorted(self.messages, key=lambda x: x["timestamp"])

            except socket.error as e:
                print(f"Error connecting to peer: {e}")
            except e:
                print(f"Something went wrong: {e}")
        self.dumpDataToFile()

    def dumpDataToFile(self):
        dictionary = {
            "messages": self.messages,
            "peers": self.peers,
        }
        json_object = json.dumps(dictionary, indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)

    def terminateFunction(self):
        self.stop_threads = False

    def sync_peers(self):
        for peer in self.peers:
            try:
                s = socket.socket()
                s.connect(("", int(peer)))
                data = ("sync peers").encode()
                s.send(data)

                peer_data = json.loads(s.recv(1024).decode())
                for p in peer_data:
                    if p not in self.peers:
                        self.peers.append(p)
                s.close()
            except socket.error as e:
                print(f"Error connecting to peer: {e}")
            except e:
                print(f"Something went wrong: {e}")
        self.dumpDataToFile()


def main():
    author = input("Enter Auther Name: ")
    messageBoard = MessageBoard(author)
    listenPeersThread = Thread(target=messageBoard.listenPeers)
    listenPeersThread.start()
    syncingThread = Thread(target=messageBoard.syncAfterInterval, args=(5,))
    syncingThread.start()
    listeningPort = input("Port to get messages or enter to pass: ")

    messageBoard.connect(listeningPort)
    while True:
        print("Enter 0 to terminate")
        print("Enter 1 to Add the message")
        print("Enter 2 to print the messages")
        print("Enter 3 to print the peers")
        print("Enter 4 to sync the message")
        print("Enter 5 to sync the peers")
        print("Enter 6 to connect to the peer")

        option = input("Enter option: ")
        if option == "0":
            messageBoard.terminateFunction()
            break
        elif option == "1":
            message = input("Enter the message")
            messageBoard.add_message(message)
        elif option == "2":
            messageBoard.printMessages()
        elif option == "3":
            messageBoard.printPeers()
        elif option == "4":
            messageBoard.sync_messages()
            messageBoard.printMessages()

        elif option == "5":
            messageBoard.sync_peers()
            messageBoard.printPeers()
        elif option == "6":
            messageBoard.connect_peer()
        else:
            print("Please enter valid option")

    print("Waiting for the thread...")
    listenPeersThread.join()
    syncingThread.join()


main()
