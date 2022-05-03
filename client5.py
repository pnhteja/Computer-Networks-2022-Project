from ctypes import sizeof
from email import message
import pickle
import socket
import sys
import threading
import tkinter
import globals as g
import ast


clientNo = 5


sessionTable={}
is_random_agent=False

prevIpAddr = ""
prevPort = ""

SIZE = 1024*2

hostName = socket.gethostname()
clientHostName= socket.gethostbyname(hostName)



"""---------------------Connecting to Central Server---------------------"""
# TCP Socket
clientSocket_CS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket_CS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

centralServIpAddr = input("Please provide the Central Server IP Address : ")
centralServIpPort = 1024
centralServInfo = (centralServIpAddr, centralServIpPort)

clientSocket_CS.connect(centralServInfo)
print("Connected to Centralised Server...")
"""----------------------------------------------------------------------"""



"""---------------------Sending Client Details - Name, FilesList---------------------"""
clientName = input("Please enter your Name : ")
# Sending name to central server
clientSocket_CS.send(bytes(clientName,"utf-8"))

print("Sending files list to server...")

# Sending in pickle format and client files are present in globals
clientSocket_CS.send(g.toBytes(g.clientFiles[clientNo]))
"""----------------------------------------------------------------------------------"""



"""---------------------Receiving UUID---------------------"""
# Receiving client UUID from central server
clientUUID = (clientSocket_CS.recv(1024)).decode("utf-8")
print("Your (Client) UUID is : {}".format(clientUUID))
"""--------------------------------------------------------"""



"""-------------------------------UDP Socket-------------------------------"""
# udp_client1_port = 20001
clientUDPSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
clientUDPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

clientUDPInfo = (clientHostName, g.clientUDPport[clientNo])
clientUDPSocket.bind(clientUDPInfo)
print("UDP connection is up & listening...")

# Sending UDP info to central server in pickled format
clientSocket_CS.send(bytes("UDP_ADDR:" + clientUDPInfo[0] + ":" + str(clientUDPInfo[1]),"utf-8"))
"""------------------------------------------------------------------------"""




# Receiving messages from UDP connection (left and right neighbours)
# Receives only pickled data
def udpreceiveMsg():

	while True:

		message = clientUDPSocket.recvfrom(SIZE)
		message = message[0]
		message = pickle.loads(message)

		if (message["type"] == "query"):

			#---------------------------------#
			print("Received Query Packet...")
			#---------------------------------#

			if (message["hopCount"] > 0):
				
				message["hopCount"] = message["hopCount"] - 1
				
				if(message["hopCount"] > 0):
					#----------------------------------------------------#
					print("Hopcount not zero sending to right neighbour")
					#----------------------------------------------------#
					data = pickle.dumps(message)
					clientUDPSocket.sendto(data, g.rightNeighbourAddr[clientNo])
				
				elif(message["hopCount"] == 0):
					#----------------------------------------------------#
					print("Qeury hit recorded.....")
					#----------------------------------------------------#
					message["type"]="queryHit"
					message["sourceUUID"] = clientUUID
					message["ipaddr"]=clientUDPInfo[0]
					message["port"]=clientUDPInfo[1]
					data = pickle.dumps(message)

					if(message["reverseHopCount"] > 0):
						clientUDPSocket.sendto(data, g.rightNeighbourAddr[clientNo])
					elif(message["reverseHopCount"] < 0):
						clientUDPSocket.sendto(data, g.leftNeighbourAddr[clientNo])

			elif (message["hopCount"] < 0):

				message["hopCount"] = message["hopCount"] + 1
				
				if(message["hopCount"]<0):
					#----------------------------------------------------#
					print("Hopcount not zero sending to left neighbour")
					#----------------------------------------------------#
					data = pickle.dumps(message)
					clientUDPSocket.sendto(data, g.leftNeighbourAddr[clientNo])

				elif(message["hopCount"] == 0):
					#----------------------------------------------------#
					print("Qeury hit recorded.....")
					#----------------------------------------------------#
					message["type"]="queryHit"
					data=pickle.dumps(message)

					if(message["reverseHopCount"] > 0):
						clientUDPSocket.sendto(data, g.rightNeighbourAddr[clientNo])
					elif(message["reverseHopCount"] < 0):
						clientUDPSocket.sendto(data, g.leftNeighbourAddr[clientNo])
		
		elif (message["type"] == "queryHit"):

			if(is_random_agent):
				sessionTable[message["sourceUUID"]]={}
				sessionTable[message["sourceUUID"]]["ipaddr"]=message["ipaddr"]
				sessionTable[message["sourceUUID"]]["port"]=message["port"]
				message["ipaddr"]=clientUDPInfo[0]
				message["port"]=clientUDPInfo[1]


			if (message["reverseHopCount"] > 0):

				message["reverseHopCount"] = message["reverseHopCount"] - 1
				
				if(message["reverseHopCount"] > 0):
					#----------------------------------------------------#
					print("Reverse Hopcount not zero sending to right neighbour")
					#----------------------------------------------------#
					data = pickle.dumps(message)
					clientUDPSocket.sendto(data, g.rightNeighbourAddr[clientNo])
				
				elif(message["reverseHopCount"] == 0):
					print("Successfully received queryHit packet back !!!")
					prevIpAddr = ""
					prevPort = ""
					requestPacket={}
					requestPacket["type"]="request"
					requestPacket["desUUID"]=message["sourceUUID"]
					requestPacket["ipaddr"]=clientUDPInfo[0]
					requestPacket["port"]=clientUDPInfo[1]
					requestPacket["fileName"]=g.reqFile
					data=pickle.dumps(requestPacket)
					clientUDPSocket.sendto(data, (message["ipaddr"], message["port"]))


			elif (message["reverseHopCount"] < 0):
				
				message["reverseHopCount"] = message["reverseHopCount"] + 1

				if(message["reverseHopCount"] < 0):
					#----------------------------------------------------#
					print("Reverse Hopcount not zero sending to left neighbour")
					#----------------------------------------------------#
					data = pickle.dumps(message)
					clientUDPSocket.sendto(data, g.leftNeighbourAddr[clientNo])
				
				elif(message["reverseHopCount"] == 0):
					print("Successfully received queryHit packet back !!!")
					prevIpAddr = ""
					prevPort = ""
					requestPacket={}
					requestPacket["type"]="request"
					requestPacket["desUUID"]=message["sourceUUID"]
					requestPacket["ipaddr"]=clientUDPInfo[0]
					requestPacket["port"]=clientUDPInfo[1]
					requestPacket["fileName"]=g.reqFile
					data=pickle.dumps(requestPacket)
					clientUDPSocket.sendto(data, (message["ipaddr"], message["port"]))

		elif(message["type"]=="request"):
			if(message["desUUID"]==clientUUID):
				print("File transfer in progress........")
				prevIpAddr = message["ipaddr"]
				prevPort = message["port"]

				receivePacket = {}
				receivePacket["type"] = "receive"
				data = pickle.dumps(receivePacket)
				clientUDPSocket.sendto(data, (prevIpAddr, prevPort))

				print("File name : {}".format(message["fileName"]))

				file = open(message["fileName"],"rb")
				data = file.read(SIZE)
				while data:
					clientUDPSocket.sendto(data, (prevIpAddr, prevPort))
					data = file.read(SIZE)
				file.close()

				print("Success 1 !!!")

			else:
				print("File not found, searching in the next agent node........")
				prevIpAddr = message["ipaddr"]
				prevPort = message["port"]
				message["ipaddr"]=clientUDPInfo[0]
				message["port"]=clientUDPInfo[1]
				data=pickle.dumps(message)
				clientUDPSocket.sendto(data, (sessionTable[message["desUUID"]]["ipaddr"], sessionTable[message["desUUID"]]["port"]))

		elif (message["type"] == "receive"):

			file = open("client-" + str(clientNo),"wb")
			data = clientUDPSocket.recvfrom(SIZE)
			file.write(data[0])
			while (len(data[0]) >= SIZE ):
				data = clientSocket.recvfrom(SIZE)
				file.write(data[0])
			file.close()

			if ( prevIpAddr != "" ):
				print("File transfer in progress........")

				receivePacket = {}
				receivePacket["type"] = "receive"
				data = pickle.dumps(receivePacket)
				clientUDPSocket.sendto(data, (prevIpAddr, prevPort))

				print("Success 2!!")

				file = open("client-" + str(clientNo),"rb")
				data = file.read(SIZE)
				while data:
					clientUDPSocket.sendto(data, (prevIpAddr, prevPort))
					data = file.read(SIZE)
				file.close()

			else:
				print("File transfer complete !!!")







# Receiving messages from TCP connection (central server) in pickled format
def receiveMsg ( msgList ):

	while True:

		message = clientSocket_CS.recv(1024)
		message = pickle.loads(message)

		# Left Neighbour
		if (message["type"] == "LEFT"):
			g.leftNeighbourAddr[clientNo] = (message["addr"], message["port"])
			msgList.insert(tkinter.END, "Left Neighbour address is {}".format(g.leftNeighbourAddr[clientNo]))

		# Right Neighbour
		elif (message["type"] == "RIGHT"):
			g.rightNeighbourAddr[clientNo] = (message["addr"], message["port"])
			msgList.insert(tkinter.END, "Right Neighbour address is {}".format(g.rightNeighbourAddr[clientNo]))

		# Hop Count
		elif ((message["type"] == "HOPCOUNT")):

			if ( type(message["hopCount"]) != str ):

				hopCount = message["hopCount"]
				
				msgList.insert(tkinter.END, "Received a hopCount of {} from the central server".format(hopCount))

				queryPacket = {}
				queryPacket["type"]="query"
				queryPacket["hopCount"] = hopCount
				queryPacket["reverseHopCount"]= 0-hopCount
				queryPacket["sourceUUID"] = clientUUID
				queryPacket["ipaddr"] = clientUDPInfo[0]
				queryPacket["port"] = clientUDPInfo[1]

				data = pickle.dumps(queryPacket)

				#------------------------------#
				print("Sending Query Packet...")
				#------------------------------#

				print(g.leftNeighbourAddr)
				print(g.rightNeighbourAddr)

				if queryPacket["hopCount"] > 0:
					clientUDPSocket.sendto(data, g.rightNeighbourAddr[clientNo])
				elif queryPacket["hopCount"] < 0:
					clientUDPSocket.sendto(data, g.leftNeighbourAddr[clientNo])

			else:
				msgList.insert(tkinter.END,'{}'.format(message["hopCount"]))

		else:
			msgList.insert(tkinter.END,'{}'.format(message))
		
		# if ( message.find("ACTIVE MEMBERS") != -1 ):
		# 	msgList.insert(tkinter.END,message)
		
		# elif ( message.find("has been added to the Chat") != -1 ):
		# 	msgList.insert(tkinter.END,'                                {}'.format(message))
		
		# elif(message.find("ID")!=-1):
		# 	msgList.insert(tkinter.END,'Your Generated {}'.format(message))
		
		
		


# Sending messages / queries to Central Server
def sendMsg ( textInput, msgList, clientSocket_CS ):

	req = textInput.get()
	textInput.delete(0, tkinter.END)

	msgList.insert(tkinter.END, "You : " + req)

	# Quitting from the Chatroom
	if ( req.find("QUIT") != -1 ):
		clientSocket_CS.send(bytes(req,"utf-8"))
		msgList.insert(tkinter.END, 'You have left the chat')
		sys.exit()

	else:
		if (req.find("FILESEND") != -1):
			g.reqFile = req.split(" ")[1]
		print("Requested File : {}".format(g.reqFile))
		clientSocket_CS.send(bytes(req,"utf-8"))




print("Transfering you to Chat Room...")


"""------------------------------------GUI START------------------------------------"""
chatWindow = tkinter.Tk()
chatWindow.title('Chatroom')

frameMsgs = tkinter.Frame(master=chatWindow)
scrollBar = tkinter.Scrollbar(master=frameMsgs)

msgList = tkinter.Listbox (
	master=frameMsgs, 
	yscrollcommand=scrollBar.set
)

scrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=False)
msgList.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

frameMsgs.grid(row=0, column=0, columnspan=5, sticky="nsew")

frameEntry = tkinter.Frame(master=chatWindow)
textInput = tkinter.Entry(master=frameEntry)
textInput.pack(fill=tkinter.BOTH, expand=True)


"""-----------------------------------------------------------------------------"""
# Sending message to Central Server
textInput.bind("<Return>", lambda x: sendMsg(textInput, msgList, clientSocket_CS) )
textInput.insert(0, "Please enter your message here")
"""-----------------------------------------------------------------------------"""


sendButton = tkinter.Button(
	master=chatWindow,
	text='send',
	command=lambda: sendMsg(textInput, msgList, clientSocket_CS)
)



frameEntry.grid(row=1, column=0, padx=10, sticky="ew")
sendButton.grid(row=1, column=1, pady=10, sticky="ew")

chatWindow.rowconfigure(0, minsize=500, weight=1)
chatWindow.rowconfigure(1, minsize=50, weight=0)
chatWindow.columnconfigure(0, minsize=500, weight=1)
chatWindow.columnconfigure(1, minsize=200, weight=0)


"""-------------------------------------GUI END-------------------------------------"""



# Requesting Central Server to send neighbours info
# clientSocket_CS.send(bytes("send ip_neigh_addr","utf-8"))




recvThread = threading.Thread(target=receiveMsg, args=(msgList,))
recvThread.daemon = True
recvThread.start()

udprecvThread = threading.Thread(target=udpreceiveMsg)
udprecvThread.daemon = True
udprecvThread.start()

msgList.insert(tkinter.END,"Welcome to the Chat Room Client {} - {}!!".format(clientNo, clientName))

chatWindow.mainloop()