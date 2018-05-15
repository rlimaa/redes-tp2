#   Trabalho Pratico 2 - Redes de Computadores
#   Emylle Alves Leitao
#   Rodrigo Lima de Araujo
#   chat_serverv5.py

import sys
import socket
import select
from struct import * #importa as bibliotecas necessarias

HOST = ''
SOCKET_LIST = []
client_id = [] #inicializa duas listas uma para o socket e uma pra os identificadores dos clientes
try:
    PORT = int(sys.argv[1]) #le o port em que o chat sera inicializado
except:
    print 'ERRO! Parametro PORT incorreto. Saindo...'
    quit()

def descon_cliente(sock, i):#funcao que desconecta o cliente
    try:
        SOCKET_LIST.remove(sock)#remove o socket da lista de sockets observados pelo select
        if i==0:
            n=client_id.index(sock)#salva o indice do socket a ser removido
            client_id.insert(n, 0)#insere um zero no indice do socket a ser removido
        client_id.remove(sock)#remove o socket do cliente desconectado
        sock.close()#fecha o socket
    except:
        pass

def send_ok(cli_id, s, num_seq): #funcao que envia o OK
    s.send(pack('!H',1)) #identificador msg ok
    s.send(pack('!H', 0xffff)) #identificador orig server
    s.send(pack('!H', cli_id)) #identificador destino cliente
    s.send(pack('!H', num_seq)) #numero de sequencia da msg confirmada

def send_error(cli_id, s, num_seq): #funcao que envia o ERROR
    s.send(pack('!H',2)) #identificador msg error
    s.send(pack('!H', 0xffff)) #identificador orig server
    s.send(pack('!H', cli_id)) #identificador destino cliente
    s.send(pack('!H', num_seq)) #numero de sequencia com erro

def chat_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10) #cria o socket do servidor
    SOCKET_LIST.append(server_socket)#insere o socket do servidor na lista de sockets a serem observados
    client_id.append(server_socket)#identificador 0 (broadcast) recebe socket servidor
    print "Chat iniciado no porto de numero " + str(PORT) #printa o port em que o chat foi inicializado
    client_index=1 #inicializa variaveis necessarias
    seq_num_server = 0
    while 1:
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0) #seleciona o socket em que informacoes serao tratadas

        for sock in ready_to_read:#loop para tratar todos os sockets que precisam de tratamento

            if sock == server_socket: #se o socket a ser tratado e o socket que abre novas conexoes
                sockfd, addr = server_socket.accept() #aceita a nova conexao
                SOCKET_LIST.append(sockfd) #insere o socket da nova conexao a lista de sockets observados para tratamento
                client_id.append(sockfd) #insere o socket da nova conexao na lista de identifcador de clientes

            # chegou uma msg
            else:
                sock.settimeout(5)
                try:
                    # recebe as primeiras informacoes do protocolo
                    temp_tuple = unpack('!H', sock.recv(2))
                    msg_type = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    orig_id = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    dest_id = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    seq_num = temp_tuple[0]
                except:
                    descon_cliente(sock)
                    continue
                if msg_type == 1:#se a msg e do tipo OK
                    if dest_id == 0xffff: #se o destino e o servidor
                        continue #continua o loop
                    else: #se o destino e outro cliente
                        fwd_msg = pack('!H', msg_type)+pack('!H', orig_id)+pack('!H', dest_id)+pack('!H', seq_num) #encaminha a msg para o cliente correto
                        s_fwd = client_id[dest_id] #socket de encaminhamento recebe o socket na lista com o identificador de origem
                        s_fwd.send(fwd_msg) #envia a msg para o socket correto
                        continue #continua o loop
                elif msg_type == 2:#se o tipo da msg e ERROR
                    if dest_id == 0xffff: #se o destino e o servidor
                        continue#continua o loop
                    else:#se e outro cliente
                        fwd_msg = pack('!H', msg_type)+pack('!H', orig_id)+pack('!H', dest_id)+pack('!H', seq_num) #encaminha a msg para o cliente correto
                        s_fwd = client_id[dest_id] #socket para encaminhamento e o determinado pelo identificador
                        s_fwd.send(fwd_msg)#envia msg encaminhada
                elif msg_type == 3:#se a msg e do tipo OK
                    if len(client_id) < 0xffff:#se o tamanho da lista de clientes e menor do que 2 bytes
                        try:
                            client_number=client_id.index(sock) #descobre o identificador do cliente a partir do indice do socket na lista
                        except:
                            send_error(client_number, sock, seq_num) #manda erro
                            descon_cliente(sock, 1) #desconecta o cliente
                        send_ok(client_number, sock, seq_num)#manda o OK
                        print "Cliente ["+str(client_number)+"] conectado com Sucesso!"#printa que o cliente foi conectado
                    else:#se a lista esta cheia
                        try:
                            client_id.remove(sock)
                            indice = client_id.index(0) #checa se tem algum identificador vago (algum cliente desconectou)
                            client_id.remove(0) #remove o zero que estava la
                            client_id.insert(indice, sock) #se sim, insere o socket novo nessa posicao
                            client_number = indice #o identificador recebe indice em que o socket foi inserido
                            print 'indice',indice
                            send_ok(client_number, sock, seq_num) #manda o OK para confirmar
                            print "Cliente ["+str(client_number)+"] conectado com Sucesso!" #printa que o cliente foi conectado
                        except: #se nao tiver posicao vaga na lista
                            send_error(client_number, sock, seq_num)#envia ERROR para o cliente que nao pode conectar
                            descon_cliente(sock, 1) #desconecta o cliente
                elif msg_type == 4:#se a msg e do tipo FLW
                    try:
                        if sock == client_id[orig_id]:#descobre se o identificador de origem e o identificador do socket
                            send_ok(orig_id, sock, seq_num)#envia o OK
                            descon_cliente(sock, 0) #desconecta o cliente
                            print 'Cliente ['+str(orig_id)+'] desconectado com Sucesso!'
                        else:  #cliente tentou se passar por outro
                            real_orig_id = client_id.index(sock) #descobre o identificador verdadeiro do cliente
                            send_error(real_orig_id, sock, seq_num) #envia msg ERROR
                    except:
                        send_error(orig_id,sock,seq_num) #envia msg de ERROR se nao foi possivel concluir o FLW
                elif msg_type == 5: #se o tipo da msg e MSG
                    temp_tuple = unpack('!H', sock.recv(2))#recebe o tamanho da msg
                    c = temp_tuple[0]#transforma para int
                    data = sock.recv(c)#recebe os dados da msg
                    fwd_msg= pack('!H', msg_type) + pack('!H', orig_id) + pack('!H', dest_id) + pack('!H', seq_num_server) + pack('!H', c)+data #cria a msg a ser encaminhada
                    try:
                        if dest_id != 0: #se o destino nao for broadcast
                            s_fwd = client_id[dest_id] #pega o socket de destino da lista de clientes
                            s_fwd.send(fwd_msg) #envia para o socket de destino
                        else:
                            broadcast(server_socket, sock, fwd_msg) #faz broadcast da msg
                        send_ok(orig_id, sock, seq_num)#envia o OK
                    except:
                        send_error(orig_id, sock, seq_num)#se deu algum problema envia ERRO
                elif msg_type == 6:#se a msg e do tipo CREQ
                    clist=[] #inicia a lista clist
                    print 'CREQ cliente '+str(orig_id)#printa a Requisicao da lista do cliente
                    for i in range(0,int(len(client_id)),1):#loop para descobrir os clientes online
                        try:
                            if (client_id[i]!=0) and (client_id[i]!=server_socket):#se a posicao do client_id nao e zero, nem o server_socket
                                print client_id[i]
                                clist.append(i)#insere o identificador na CLIST
                        except:
                            continue #se deu algum problema continua o loop
                    clist_msg = pack('!H', 7)+pack('!H', 0xffff)+pack('!H', orig_id)+pack('!H', seq_num_server)+pack('!H', len(clist)) #cria a msg a ser enviada ao cliente que requisitou a lista
                    for i in range(0,int(len(clist)),1):#loop para criar a msg CLIST
                        clist_msg = clist_msg + pack('!H',clist[i])#insere cada cliente na msg
                    sock.send(clist_msg)#envia a msg CLIST

# funcao de broadcast
def broadcast (server_socket, sock, msg):
    for socket in SOCKET_LIST:#para todos os sockets na lista de sockets observados pelo select
        if socket != server_socket and socket != sock :#se o socket nao e o servidor nem quem esta fazendo o broadcast
            try:
                socket.send(msg) #tenta enviar a msg
            except :#se algo der errado, socket corrompido
                socket.close()#fecha o socket
                if socket in SOCKET_LIST:#se o socket esta na lista de sockets observados pelo select
                    SOCKET_LIST.remove(socket) #remove da lista
                    try:
                        index = client_id.index(socket) #descobre o indice do socket corrompido
                        client_id.remove(socket) #remove o socket da lista
                        client_id.insert(index, 0) #insere um 0 no lugar
                    except: continue

if __name__ == "__main__": #inicio do programa

    sys.exit(chat_server()) #chama a funcao e sai
