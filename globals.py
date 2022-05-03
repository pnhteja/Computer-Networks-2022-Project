import pickle

# no_of_hops = []


Send_string = "FILESEND"
Send_neighbours = "NEIGHBOURS"

# agent_node=[]

reqFile = ""


clientFiles = {}
clientFiles[1] = ['file1.txt', 'file2.txt']  
clientFiles[2] = ['file3.txt', 'file4.txt']
clientFiles[3] = ['file5.txt', 'file6.txt']
clientFiles[4] = ['file7.txt', 'file8.txt']
clientFiles[5] = ['file9.txt', 'file10.txt']
clientFiles[6] = ['file11.txt', 'file12.txt']


clientUDPport = {}
clientUDPport[1] = 20001
clientUDPport[2] = 20002
clientUDPport[3] = 20003
clientUDPport[4] = 20004
clientUDPport[5] = 20005
clientUDPport[6] = 20006


leftNeighbourAddr = {}
rightNeighbourAddr = {}



def toBytes(x):
    return pickle.dumps(x)


# def hopcount(uuid, selfid, clientsid):
#     # return 2
#     for i in clientsid:
#         if(clientsid[i]==uuid):
#             return abs(selfid-i)


# def isFilePresent(file_name,dict):
#     arr=[]
#     for i in dict:
#         for j in dict[i]["files"]:
#             if j==file_name:
#                 return True, i
#     return False, 0