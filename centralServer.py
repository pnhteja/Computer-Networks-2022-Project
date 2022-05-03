import pickle
import socket
import sys
import threading
import uuid
import globals as g
import numpy as np
# import random
SIZE = 1024

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

hostName = socket.gethostname()
host_ip_addrss= socket.gethostbyname(hostName)
port = 1024
serverInfo = (host_ip_addrss, port)

serverSocket.bind(serverInfo)
serverSocket.listen()

print("Server IP Address : " + host_ip_addrss)
print("Server up and running...")
print("Hostname of server socket : " + hostName)


noOfClients = 6
clients = []
noOfClientsArrived = 0
clientAddresses = []
clientNames = []
# threads = []
clientInfo = {}
# clientsid=[]
clientsid={}
clientFilesList=[]


clientUUIDs={}
threads = {}
clientConn = {}



def receiveAndSendMsg ( i,t ):

    # Sending client it's UUID
    clientConn[i].send(clientUUIDs[i].encode())

    while True:

        # Waiting for client's message / query
        msg = clientConn[i].recv(1024)
        msg = msg.decode("utf-8")

        if(msg.find("UDP_ADDR")!=-1):

            msg = msg.split(":")
            print(msg)
            clientInfo[clientUUIDs[i]]["UDPInfo"] = (msg[1], int(msg[2]))
        
        # Client's query for neighbours info 
        elif(msg.find(g.Send_neighbours)!=-1):
            
            if(i > 1):
               
                leftNeighbour = {}
                leftNeighbour["type"] = "LEFT"
                leftNeighbour["addr"] = clientInfo[clientUUIDs[i-1]]["UDPInfo"][0]
                leftNeighbour["port"] = clientInfo[clientUUIDs[i-1]]["UDPInfo"][1]
                data = pickle.dumps(leftNeighbour)
                clientConn[i].send(data)


                # Sending current client's address to previous client
                rightNeighbour = {}
                rightNeighbour["type"] = "RIGHT"
                rightNeighbour["addr"] = clientInfo[clientUUIDs[i]]["UDPInfo"][0]
                rightNeighbour["port"] = clientInfo[clientUUIDs[i]]["UDPInfo"][1]
                data = pickle.dumps(rightNeighbour)
                clientConn[i-1].send(data)

                                
        # Client's query for file
        elif(msg.find(g.Send_string)!=-1):

            fileName = msg.split(" ")[1]
            g.reqFile = fileName

            print("Requested file in globals : {}".format(g.reqFile))

            isFilePresent = False
            hopCount = 0

            for cltUUID in clientInfo.keys():
                for f in clientInfo[cltUUID]["files"]:
                    if ( f == fileName ):
                        isFilePresent = True
                        hopCount = clientInfo[cltUUID]["clientNo"] - i
                        break

            # g.agent_node.append(random.randint(i, i+hopCount))

            HOPCOUNT = {}
            HOPCOUNT["type"] = "HOPCOUNT"
            
            if ( isFilePresent ):
                print("File requested by Client {} found at Client {}".format(i, hopCount+i))
                HOPCOUNT["hopCount"] = hopCount
            else:
                print("File requested by Client {} is not present".format(i))
                HOPCOUNT["hopCount"] = "File not present"

            data = pickle.dumps(HOPCOUNT)
            clientConn[i].send(data)



# Accepting connections from clients
for i in range(1, noOfClients+1):

    client, addr = serverSocket.accept()
    port_client = addr[1]

    # After accepting connection, client sends it's name
    clientName = client.recv(SIZE).decode("utf-8")
    
    # Client sends it's files list, unpickling the array of filenames
    clientFiles = pickle.loads(client.recv(SIZE))
    
    # Generating UUID for client based on it's port number which is unique (since same host) 
    clientUUID = str(uuid.uuid5(uuid.NAMESPACE_URL, str(port_client)))

    # Updating most used quantities
    clientUUIDs[i] = clientUUID
    clientConn[i] = client
    
    clientInfo[clientUUID] = {}
    clientInfo[clientUUID]["clientNo"] = i
    clientInfo[clientUUID]["name"] = clientName
    clientInfo[clientUUID]["connection"] = client
    clientInfo[clientUUID]["address"] = addr[0]
    clientInfo[clientUUID]["port"] = addr[1]
    clientInfo[clientUUID]["status"] = "active"
    clientInfo[clientUUID]["files"] = clientFiles


    #----------------------------------------------------------------------#
    print("Connected with Client {}".format(i))
    print("Client Name : {}".format(clientName))
    print("Client IP Addr : {}".format(addr[0]))
    print("Client Port : {}".format(addr[1]))
    print("Client Status : {}".format(clientInfo[clientUUID]["status"]))
    print("Client Files : {}".format(clientFiles))
    #----------------------------------------------------------------------#


    # Thread for futher communication with client either sending or receiving
    threads[i] = threading.Thread(target=receiveAndSendMsg,args=(i,6556))
    threads[i].daemon = True
    threads[i].start()


for i in range(1, noOfClients+1):
	threads[i].join()