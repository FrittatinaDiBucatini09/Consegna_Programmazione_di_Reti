#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 00:06:50 2024

@author: riccardobalzani
0001090902
"""

import socket
import threading 
import sys
import time
import tkinter as tkt


MAX_ATTEMPTS = 3
DELAY = 0.1
BUFSIZ = 1024   # Dimensione massima messaggio 1 Kb
HOST = 'localhost'
PORT = 8080
SERVER_CLOSED= "Server: Server disconnected type something to quit..."

server_address = (HOST, PORT)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Inizializzo il socket

# Variabili globali gui
root = tkt.Tk()
message = tkt.StringVar()
messages_frame = tkt.Frame(root)
scrollbar = tkt.Scrollbar(messages_frame)
message_list = tkt.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)

first_message = True    # Il primo messaggio indica il nome 
kill_thread = False     # Stoppa il thread

receiving_thread_lock = threading.Lock()    # Protegge le variabili condivise con la gui

# Riceve i messaggi 
def receive_message(event=None):
    global kill_thread
    
    while True:
        try:
            message_received = client_socket.recv(BUFSIZ).decode("utf8")
            
            with receiving_thread_lock:
                message_list.insert(tkt.END, message_received)  # Fa apparire a schermo il messaggio ricevuto
            
            if(message_received == SERVER_CLOSED):
                break
                
            else:
                print(message_received)
            
            if kill_thread: # Il programma è terminato
                break
            
        except Exception as e:  # Eccezione nel ricevimento dei messaggi
            print("Error receiving message: ", e)
            break
        
        kill_thread = True
    
    
    
def send_message(event=None):
    attempts = 0    # Tentativi di invio
    global first_message
    
    while attempts <= MAX_ATTEMPTS:     # Massimo numero di tentativi
        attempts += 1
        
        try:
           message_to_send = message.get()  # Cattura messaggio
           message.set("")
           
           if message_to_send == 'exit':    # Chiusura client
               close_client()
               break
           
           if first_message:
               if message_to_send.lower() == 'server':  # Nome utente non valido
                   with receiving_thread_lock:
                       message_list.insert(tkt.END, "Change your name...")
                       
                   break
               
               else:
                   with receiving_thread_lock:
                       message_list.insert(tkt.END, "Welcome " + message_to_send + " :)")   # Benvenuto
                
                   first_message = False
                    
           client_socket.send(message_to_send.encode()) # Invio messaggio al server
        
        except BrokenPipeError as b:    # Errore irreparabile
            print("Error sending message: ", b)
            close_client()
            break
        
        except Exception as e:  # Eccezione generica provoca un nuovo tentativo 
            print("Error sending message: ", e)
            
            if attempts >= MAX_ATTEMPTS:
                print("Max attempts reached...")
                close_client()
                break
            
            else:
                wait() # Dopo 0.1 secondi si ha un nuovo tentativo

            
# Fa partire la gui    
def start_gui():
    root.title("Chat")
    
    scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)  # Configura la scrollbar
    
    # Configura la lista dei messaggi
    message_list.pack(side=tkt.LEFT, fill=tkt.BOTH)
    message_list.pack()
    messages_frame.pack()
     
    # Configura il campo di inserimento
    entry_field = tkt.Entry(root, textvariable=message)
    entry_field.bind("<Return>", send_message)
    entry_field.pack()
    
    # Configura il send_button
    send_button = tkt.Button(root, text="Invio", command=send_message)
    send_button.pack()
    
    root.protocol("WM_DELETE_WINDOW", close_client) # Gestisce la chiusura della finestra 
    
    # Istruzioni del server 
    with receiving_thread_lock:
        message_list.insert(tkt.END, "Insert your name in the text box...")
        message_list.insert(tkt.END, "Type exit to quit...")
    
    root.mainloop() # Avvia il loop principale della gui
    
# Attesa tra nuovi tentativi      
def wait():
    print("New attempt...")
    time.sleep(DELAY)
    
# Chiusura del client    
def close_client(event=None):
    root.after(1000, root.destroy())
    
    global kill_thread
    
    if not kill_thread:
        kill_thread = True
    
    client_socket.close()
    
    
    root.quit()
    sys.exit()
    
    
receiving_thread = threading.Thread(target=receive_message) # Inizializzazione receiving_thread


# main function
def main():
    connection_attempts = 0
    global kill_thread
    
    while not kill_thread:
        connection_attempts += 1    # Massimo numero di tentativi
        
        try:
            client_socket.connect(server_address)   # Connessione al server
            receiving_thread.start()    # Avvio closing_thread
            start_gui()     # Avvio gui
            
        except ConnectionRefusedError as r:     # Errore che può non ricorrere
            print("Server is full. Connection rejected.")
            
            if connection_attempts >= 3:    # Massimo numero di tentativi raggiunto
                print("Max attempts reached...")
                print("Errore connecting to server: ", r)
                close_client()
                break
            
            else:   
                connection_attempts = connection_attempts + 1    
                wait()  # Tentativo di riconnessione
                
        except Exception as e:
            print("Error:", e)
            close_client()
            break
        
    
if __name__ == "__main__":
    main()

        
        