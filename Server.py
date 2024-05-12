#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 00:06:50 2024

@author: riccardobalzani
"""


import socket
import threading
import time
import sys


MAX_ATTEMPTS = 3    # Massimo numero di tentativi
DELAY = 0.1     # Ritardo tra nuovi tentativi
BACKLOG = 5     # Coda di backlog
BUFSIZ = 1024   # Dimensione massima messaggio 1 Kb
HOST = 'localhost'
PORT = 8080
SERVER_CLOSED = "Server: Server disconnected type exit to quit..."   # Messaggio di chiusura del server

server_address = (HOST, PORT)

# Gestione della lista dei client
client_list = []
client_list_lock = threading.Lock()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Server del socket


# Gestione del client
def handle_client(client):
    name = None
    
    while True:
        try:
            if not name:    # Il primo messaggio ricevuto indica il nome del client
                name = client.recv(BUFSIZ).decode("utf8")
                if name:
                    print('\n' + name + " is ", client.getpeername())
                
            else:
                message = client.recv(BUFSIZ).decode("utf8")    # Riceve i messaggi dal client
                if message == 'exit':
                    disconnect_client(client)
                    
                if message:
                    message = name + ": " +  message    # Aggiunge il nome al messaggio
                    print('\n' + message)
                
                    send_to_all_clients(message)    # Invia il messaggio a tutti i client connessi
                
        except Exception as e:  # Un errore di ricezione provoca la disconnessione del client
            print("\nError receiving message: ", e)
            
            with client_list_lock:  # La lista va acceduta in mutua esclusione
                disconnect_client(client)
            break


# Invia il messaggio a tutti i client connessi
def send_to_all_clients(message):
    with client_list_lock:
        for client in client_list:
            attempts = 0
            
            while True:
                attempts += 1
                
                try:
                    client.send(message.encode())   # Invia il messaggio al client
                    break
                
                except BrokenPipeError as b:    # Eccezione BrokenPipe provoca la disconnessione
                    print("\nError sending message to: ", str(client.getpeername()))
                    print("\nError type: ", b)
                    
                    with client_list_lock:
                        disconnect_client(client)
                    break
                    
                except Exception as e:  # Eccezione generica provoca un nuovo tentativo
                    print("\nError sending message to: ", e)
                    print("\nError type: ", e)
                    
                    if attempts >= MAX_ATTEMPTS:    # Massimo numero di tentativi raggiunto
                        
                        with client_list_lock:
                            disconnect_client(client)
                        break
                    
                    else:
                        wait()  # Attesa tra un tentativo e il successivo


# Disconnette il client
def disconnect_client(client):
    if client.fileno() != -1:   # Controlla che la connessione sia ancora attiva
        client.close()
    
    if client in client_list:   # Controlla che il client sia ancora nella client_list
        client_list.remove(client)


# Attesa tra nuovi tentativi
def wait():
    print("\nNew attempt...")
    time.sleep(DELAY)


# Chiude il server
def close_server(event=None):
    close = ''
    
    time.sleep(5)
    
    while not close == 'close':     # Messaggio di chiusura
        close = input("\n")
        
    
    send_to_all_clients(SERVER_CLOSED)  # Invia il messaggio di chiusura a tutti i client
    
    
    with client_list_lock:      # Disconnette tutti i client
        for client in client_list:
            disconnect_client(client)
            
    
    server_socket.close()   # Chiude il server
    print("\nServer has been closed...")
    
    sys.exit()
    


# main function
def main():
    server_socket.bind(server_address)
    server_socket.listen(BACKLOG)
    
    threading.Thread(target=close_server).start()   # Avvia il thred che recepisce il messaggio di chiusura
    
    print("\nServer created...")
    
    while True:
        print("\nWaiting for connections...")
        try:
            connections_socket, client_address = server_socket.accept()     # Accettazione connessione di un client

            with client_list_lock:
                client_list.append(connections_socket)  # Aggiunta alla lista dei client
                
            threading.Thread(target=handle_client, args=(connections_socket, )).start()     # Avvio thread del client
            
            print("\nClient connected: ", client_address)
            
        except Exception as e:
            print("\nError during server execution: ", e)
            break
    
    
if __name__ == "__main__":
    main()
                   
