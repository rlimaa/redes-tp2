#   Trabalho Pratico 2 - Redes de Computadores
#   Emylle Alves Leitao
#   Rodrigo Lima de Araujo
#   chat_clientv5.py

import sys
import socket
import select
from struct import * #importa as bibliotecas necessarias


def send_oi(s): #funcao que envia o OI
    s.send(pack('!H',3)) #identificador msg ok
    s.send(pack('!H', 0)) #ainda nao sei o meu identificador
    s.send(pack('!H', 0xffff)) #identificador destino server
    s.send(pack('!H', 0)) #numero de sequencia 0

def send_ok(my_id, cli_id, s, seq_num): #funcao que envia o OK
    s.send(pack('!H',1)) #identificador msg ok
    s.send(pack('!H', my_id)) #identificador orig
    s.send(pack('!H', cli_id)) #identificador destino cliente
    s.send(pack('!H', seq_num)) #numero de sequencia nao alterado

def send_error(my_id, cli_id, s, seq_num): #funcao que envia o ERROR
    s.send(pack('!H',2)) #identificador msg error
    s.send(pack('!H', my_id)) #identificador orig
    s.send(pack('!H', cli_id)) #identificador destino cliente
    s.send(pack('!H', seq_num)) #numero de sequencia nao alterado

def chat_client():
    try: #recebe os parametros para conexao
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
    except:
        print 'ERRO! Parametros HOST e/ou PORT incorretos! Saindo...'
        quit()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #cria socket
    #s.settimeout(2)

    # connect to remote host

    try :
        s.connect((HOST, PORT)) #conecta ao socket do servidor
        send_oi(s) #tenta entrar no chat
    except socket.settimeout:
        print 'Erro na conexao. Saindo...'
        sys.exit()

    print 'Conectado ao servidor!\n'
    print 'Para enviar msg para o destino digite no seguinte modelo:\n'
    print '<destino>,,<tipo da msg>,,<corpo da mensagem>\n'
    print 'Tipo da msg pode ser: CREQ, FLW ou MSG\n'
    print '<destino> pode ser o numero de um cliente dado pela lista de Clientes requisitada por CREQ ou 0 para broadcast.\n'
    print 'A msg do tipo CREQ requisita os clientes online no momento.\n'
    print 'A msg do tipo FLW desconecta do chat.\n'
    print 'No caso de mensagem do tipo CREQ ou FLW os campos <destino> e <corpo da mensagem> podem ter qlqr valor, mas serao ignorados\n'
    #prints de instrucoes para utilizacao do chat
    meu_seq_num = 1 #incializa variaveis
    my_id = 0
    flag_meu_numero = 0
    flw_seq_num = -1

    socket_list = [sys.stdin, s] #lista de sockets que seram observados pelo select

    while 1: #loop infinito
        if meu_seq_num == 0xffff: #se o numero de sequencia precisar de mais de dois bytes, reinicializa
            meu_seq_num=0

        ready_to_read,ready_to_write,in_error = select.select(socket_list , [], []) #seleciona o socket que sera lido

        for sock in ready_to_read: #loop para tratar todos os sockets que chamaram
            if sock == s:
                # se a mensagem esta chegando do servidor
                try:
                    temp_tuple = unpack('!H', sock.recv(2))
                    msg_type = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    orig_id = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    dest_id = temp_tuple[0]
                    temp_tuple = unpack('!H', sock.recv(2))
                    seq_num = temp_tuple[0]
                    #recebe os dados padrao do protocolo
                    if msg_type == 1: #se a mensagem for do tipo OK
                        if flag_meu_numero == 0: #se ainda nao sei meu identificador
                            my_id = dest_id #meu identificador e o destino da mensagem
                            print '>> Eu sou o numero [' + str(my_id)+']' #printa meu identificador
                            flag_meu_numero=42 #muda a flag para entrar aqui so no primeiro OK
                        if flw_seq_num == seq_num: #se a msg confirmada foi um FLW
                            print '>> Saindo ...' #encerra o programa (socket fechado pelo servidor)
                            quit()

                    if msg_type == 2: #se for mensagem de erro
                        if seq_num == 0: #se a mensagem de erro foi o OI
                            print "Erro. Nao foi possivel conectar ao Servidor. Saindo ..." #informa o erro ao usuario e sai
                            quit()
                    elif msg_type == 5: # se a mensagem e do tipo MSG
                        try:
                            temp_tuple = unpack('!H', sock.recv(2))#recebe o tamanho da msg
                            c = temp_tuple[0]#transforma em int para tratamento
                            data = sock.recv(c)#recebe os dados da msg
                            print('>> msg de [' + str(orig_id) + ']:'+data);#printa mensagem na tela do cliente
                            send_ok(my_id, orig_id, sock, seq_num) #responde com ok

                        except:
                            send_error(my_id, orig_id, sock, seq_num) #deu erro na transmissao

                    elif msg_type == 7: #se a msg for do tipo CLIST
                        try:
                            temp_tuple = unpack('!H', sock.recv(2)) #recebe o numero de clientes conectados
                            n=temp_tuple[0] #converte para int para tratamento
                            i=0 #inicializa a variavel de iteracao
                            print('>> LISTA DE CLIENTES ONLINE:')
                            print('>> Numero do Cliente\t|\tID do Cliente') #printa cabecalho da lista de clientes
                            while i < n: #loop para printar a lista
                                temp_tuple = unpack('!H',sock.recv(2)) #recebe um cliente
                                cli_num = temp_tuple[0] #converte para int
                                print('>> \t'+str(i)+':\t'+'\t|\t' + '\t'+ str(cli_num)) #printa uma linha da lista de clientes
                                i+=1 #incrementa a variavel de iteracao
                            print('>> Fim da Lista'); #printa o fim da lista
                            send_ok(my_id, orig_id, sock, seq_num) #manda o OK para o servidor


                        except:
                            send_error(my_id, orig_id, sock, seq_num) #manda ERROR se nao foi possivel receber a lista

                except:#se deu problema ao receber msgs do servidor
                    print '>> Desconectado do Servidor.'
                    sys.exit() #printa o erro e sai
            else :
                # usuario inseriu uma mensagem
                try:
                    raw_msg = sys.stdin.readline()#le uma linha
                    dest, tipo_msg, data = raw_msg.split(',,')#divide a linha nos campos destino, tipo da msg e dados
                except:
                    print 'Padrao de msg Incorreto!'
                    continue
                if tipo_msg == 'MSG': #se o tipo da msg e MSG
                    c=len(data) #variavel do tamanho da msg recebe o tamanho dos dados lidos
                    s_msg = pack('!H', 5)+ pack('!H', my_id) + pack('!H', int(dest)) + pack('!H', meu_seq_num) + pack('!H', c) + data #cria msg no padrao do protocolo com pack
                    s.send(s_msg) #manda a msg
                    meu_seq_num+=1 #incrementa o numero de sequencia
                elif tipo_msg == 'CREQ': #se o tipo de msg e CREQ
                    s_msg = pack('!H', 6)+ pack('!H', my_id) + pack('!H', 0xffff) + pack('!H', meu_seq_num) #cria a msg no padrao do protocolo, destino do CREQ sempre e o servidor 0xffff
                    s.send(s_msg)#envia a msg
                    meu_seq_num+=1#incrementa o numero de sequencia
                elif tipo_msg == 'FLW':#se o tipo de msg e FLW
                    s_msg = pack('!H', 4)+ pack('!H', my_id) + pack('!H', 0xffff) + pack('!H', meu_seq_num) #cria a msg no padrao do protocolo, destino do FLW sempre e o servidor 0xffff
                    s.send(s_msg)#envia a msg
                    flw_seq_num = meu_seq_num #guarda o numero de sequencia da msg FLW



if __name__ == "__main__":#inicio do codigo

    sys.exit(chat_client())#chama a funcao chat_client() e encerra
