import serial
import socket
import sqlite3
import sys
import time
from datetime import datetime
import select

#-----------------------------------------------------------------------------
 # Buscar puertos series disposibles. 
 # ENTRADAS:
 #   -num_ports : Numero de puertos a escanear. Por defecto 20
 #   -pruebas   : Modo verboso True/False. Si esta activado se va 
 #                imprimiendo todo lo que va ocurriendo
 # DEVUELVE: 
 #    Una lista con todos los puertos encontrados. Cada elemento de la lista
 #    es una tupla con el numero del puerto y el del dispositivo 
 #-----------------------------------------------------------------------------
def scan(num_ports = 20, pruebas=True):
    
     #-- Lista de los dispositivos serie. Inicialmente vacia
     dispositivos_serie = []
     
     if pruebas:
       print ("Escanenado %d puertos serie:" % num_ports)
     
     #-- Escanear num_port posibles puertos serie
     for i in range(num_ports):
     
       if pruebas:
         print("puerto %s: " % i)
         
       try:
       
         #-- Abrir puerto serie
         s = serial.Serial('/dev/ttyACM%s' %i)
         
         if pruebas: print ("OK --> %s" % s.portstr)
         
         #-- Si no hay errores, anadir el numero y nombre a la lista
         dispositivos_serie.append( (i, s.portstr))
         
         #-- Cerrar puerto
         s.close()
             
       #-- Si hay un error se ignora      
       except:
         if pruebas: print ("NO")
         pass
         
     #-- Devolver la lista de los dispositivos serie encontrados    
     return dispositivos_serie

#------------------------------------------------------------------------
#    Fin de la funcion scan
#------------------------------------------------------------------------


#-----------------------------------------------------------------------------
 # Leer datos de configuracin del archivo. 
 # ENTRADAS:
 #   
 # DEVUELVE: 
 #    Una lista con todos los datos encontrados. Cada elemento de la lista
 #    es una tupla con el nombre del dato y su valor 
 #-----------------------------------------------------------------------------

def lecturaParametros():

     valores = []
     infile = open('configTrama.ini', 'r')
     # fichero abierto, se lee:
     for line in infile:
         if line[0] != "#":
              campo = line[:line.find('=')]
              valor = line[line.find('=')+1:]
              valores.append((campo,valor))
         else:
              print("Comentario: " + line)
     # Cerramos el fichero.
     infile.close()
     return valores

#------------------------------------------------------------------------
#    Fin de la funcion lecturaParametros
#------------------------------------------------------------------------

#-----------------------------------------------------------------------------
 # Escribir en el archivo de LOG. 
 # ENTRADAS:
 #   -mensaje : mensaje a escribir
 #   
 #-----------------------------------------------------------------------------

def log(mensaje):

     outfile = open("configTrama.log", "a")
     # fichero abierto, se escribe el mensaje:
     ahorita = datetime.now()
     ahora = ahorita.strftime("%d/%m/%Y") + " - " + ahorita.strftime("%H:%M:") + ahorita.strftime("%s")[len(ahorita.strftime("%s"))-2:] + ": "
     outfile.write(ahora + " - " + mensaje +"\n")
      
     
     # Cerramos el fichero.
     outfile.close()

#------------------------------------------------------------------------
#    Fin de la funcion lecturaParametros
#------------------------------------------------------------------------

#-----------------------------------------------------------------------------
 # Si se pasa un id de locomotora correcto, sobreescribir en el archivo la Identificacin de locomotora.
 # Si el id es el de error se lee el id actual del archivo y se devuelve
 # ENTRADAS:
 #   -idLoco : Identificador de la locomotora
 #   
 # DEVUELVE: 
 #    El id de la locomotora actualizado   
 #-----------------------------------------------------------------------------

def correctoId(idLoco):

     if(idLoco == "XX"):
          infile = open("idLocomotora.ini", "r")
          # Leer id de la locomotora del fichero
          idLoco = infile.readline()
          # Cerramos el fichero.
          infile.close()
          
     else:
          outfile = open("idLocomotora.ini", "w")
          # fichero abierto, se sobreescribe el mensaje:
          outfile.write(idLoco)          
          # Cerramos el fichero.
          outfile.close()
     return idLoco     

#------------------------------------------------------------------------
#    Fin de la funcion correctoId
#------------------------------------------------------------------------

pruebas = True
PUERTO_CCT = 30005
PUERTO_EMB = 3355
PUERTO_GPS = 3344
PUERTO_EMBGPS = 3366
IP_CCT = '192.168.2.91'
IP_EMB = '192.168.62.20'
IP_GPS = '192.168.62.25'
SEGUNDOS_CCT = 10
SEGUNDOS_EMBARCADO = 1
SEGUNDOS_BD = 1
DIAS_BD = 2
idLocomotora = "XX"
maxRegistros = 86400

##   Inicializar el archivo del LOG
outfile = open("configTrama.log", "w")
outfile.close()

log(" Iniciando:")

parametros=lecturaParametros()
if len(parametros)!=0:
     for c,v in parametros:
          if c=='PUERTOCCT':
               PUERTO_CCT = int(v)
          elif c=="PUERTOEMB":
               PUERTO_EMB = int(v)
          elif c=="IPCCT":
               IP_CCT = v
          elif c=="IPEMB":
               IP_EMB = v
          elif c == "IPGPS":     
               IP_GPS = v
          elif c=="PUERTOGPS":
               PUERTO_GPS = int(v)
          elif c=="PUERTOEMBGPS":
               PUERTO_EMBGPS = int(v)
          elif c=="SEGUNDOSCCT":
               SEGUNDOS_CCT = int(v)
          elif c=="SEGUNDOSEMBARCADO":
               SEGUNDOS_EMBARCADO = int(v)
          elif c=="SEGUNDOSBD":
               SEGUNDOS_BD = int(v)
          elif c=="DIASBD":
               DIAS_BD = int(v)
               maxRegistros = 86400 * DIAS_BD
          if pruebas:
               print ("Parametros:  %s = %s" % (c,v))
else:
     log("  Error -> No se ha localizado el Archivo con parmetros")
     if pruebas:
          print ("  Error -> No se ha localizado el Archivo con parmetros")


###################
#Conex del Arduino:
###################          
puertos_disponibles=scan(num_ports=10,pruebas=True)
if len(puertos_disponibles)!=0:
     for n,nombre in puertos_disponibles:
          puertoSerie = nombre
          log("Microcontrolador GEIT localizado en:  %s" % nombre)
          if pruebas:
               print ("Microcontrolador GEIT localizado en:  %s" % nombre)
else:
     log("  Error -> No se ha localizado el Microcontrolador GEIT")
     if pruebas:
          print ("  Error -> No se ha localizado el Microcontrolador GEIT")
          
arduino = serial.Serial(nombre,baudrate=115200)

####################
#Definir losSockets:
####################
semb = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # para conex a embarcado es TCP
scct = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # para conex al CCT es UDP
sOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # para conex al Embarcado gps es UDP

##########################
#Conex a la base de datos:
##########################
con = None

#Abrir la base de datos:
try:
     con = sqlite3.connect('tramas.db')
     cur = con.cursor()
     cur = con.execute("SELECT * FROM datos ORDER BY num ASC")
     #cur.fetchone()
     for i in cur:
          if pruebas:
               print("En base de datos: ", i[0], i[1])
          try:
               tupla = (IP_CCT,  PUERTO_CCT)
               log("conexi al CCT: " + str(tupla))
               scct.bind((IP_CCT,  PUERTO_CCT))
               print('Conectar: %s ' %(str((IP_CCT,  PUERTO_CCT))))


               ##   Comprobar conex. del CCT:
               scct = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # para conex al CCT es UDP                         
               scct.sendto(i[1].encode('utf-8'), (IP_CCT, PUERTO_CCT))
               if pruebas:
                         print("DELETE FROM datos WHERE (num = %s)" % i[0])
               con.execute("DELETE FROM datos WHERE (num = %s)" % i[0])
               con.commit()
               if pruebas:
                    print("Eliminada TRAMA %s" % i[0])
               log("Enviada y borrada la trama: %s" % i[0])     
          except:
               scct.close()
               e = sys.exc_info()[0]
               e1 = sys.exc_info()[1]
               log('Error al <====> BORRAR TRAMA %s - %s' %(e, e1))
               if pruebas:
                    print('Error al <====> BORRAR TRAMA %s - %s' %(e, e1))
                    
   
except sqlite3.Error:
     log("Error al abrir la base de datos: %s" % e.args[0])
     if pruebas:
          print("Error al abrir la base de datos: %s" % e.args[0])          


##############
#Conex del GPS
##############          

log("Esperando conex entrante GPS")
print("Esperando conex entrante GPS") 
time.sleep(180)
try:
     ## Socket de lectura de datos del GPS:
     sIn = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
     #Con el metodo bind le indicamos que servidor y puerto 
     #sIn.bind(("192.168.1.20", 3344))
     tupla = (IP_GPS,  PUERTO_GPS)
     log("conexi al GPS: " + str(tupla))
     sIn.bind(tupla)
     #sIn.settimeout(60)
     sIn.listen(1)
     sc, addr = sIn.accept()
     
     ##Comprobar conex del GPS
     oyentesListos,escritoresListos,dudososListos = select.select([sIn],[],[],1)
     if len(oyentesListos) > 0:
          
          log("Iniciada conexi entrante GPS")

          ##Captura el ID de la locomotora de la trama GPRMC
          contComa = 0
          totalLetras = 0
          iniId = 0
          finId = 0
          idLocomotora = "XX"
          tramaGPS = sc.recv(100)
          for letra in tramaGPS.decode("utf-8"):
                       if letra == ",":
                           contComa = contComa + 1
                           if contComa == 13:
                                iniId = totalLetras+1
                                finId = totalLetras+5
                       totalLetras = totalLetras + 1
          idLocomotora = (tramaGPS.decode("utf-8"))[iniId:finId]          
     else:
          print("No se reciben datos del GPS")
          log("No se puede iniciar conexi entrante GPS")

          
     idLocomotora = correctoId(idLocomotora)
     log("Id locomotora detectada: " + idLocomotora)     
     sIn.close()
except:
     sIn.close()
     e = sys.exc_info()[0]
     e1 = sys.exc_info()[1]
     idLocomotora = correctoId(idLocomotora)
     log('Error al conectar al GPS. ID Locomotora actual = ' + idLocomotora)
     if pruebas:
          print('Error al <====> Conectar al GPS %s - %s' %(e, e1))
          
scct.shutdown     
scct.close()
semb.shutdown
semb.close()

###########################
#Bucle de lectura de datos:
###########################
texto = ''
sigo = True
tramasLogeadas = 0
ciclo = 0

#Lectura de datos recibidos desde el Microcontrolador GEIT:
recibido = texto.encode("UTF-8")

while sigo:
     ## ciclo computa las veces que se hace el while (cada segundo) para controlar cuando las operaciones
     ## se deben realizar de acuerdo a los parametros del ini
     if (ciclo < 101):
          ciclo += 1
     else:
          ciclo = 1
     time.sleep(1)
     try:
          
          while arduino.inWaiting() > 0:
                     texto = arduino.readline()
                     cuenta = 0
                     comas = 0
                     for caracter in texto.decode("utf-8"):
                          cuenta += 1
                          if caracter == ',':
                               comas += 1
                     b = texto.decode("utf-8")
                     if(tramasLogeadas < 5):
                          log("\n____________________________________________________________________________")
                          log("Recibida trama de Telemetr: " + " con %s caracteres" %cuenta)
                     if pruebas:
                          print( "Recibida trama de Telemetr: " + " con %s caracteres" %cuenta)

                     ## Recibir datos del GPS:
                     ini = 0
                     fin = 0
                     iniId = 0
                     finId = 0
                     tot = 0
                     contCo = 0
                     try: 
                          recibido = sc.recv(100)
                          if(tramasLogeadas < 5):
                               log("Recibida trama de GPS: " +recibido.decode("utf-8"))
                          if pruebas:
                               print(recibido.decode("utf-8"))
                          
                          for let in recibido.decode("utf-8"):
                            if let == ",":
                                contCo = contCo + 1                           
                                if contCo == 7:
                                    ini = tot+1
                                if contCo == 8:
                                    fin = tot
                                else:
                                 if contCo == 13:
                                      iniId = tot+1
                                      finId = tot+5
                            tot = tot + 1

                                                       
                          ## Socket para mandar cadena GPS al Embarcado
                          sOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                          log("conexi al embarado GPS: " + str((IP_EMB, PUERTO_EMBGPS)))
                          sOut.connect((IP_EMB, PUERTO_EMBGPS))
                          print('ConectarEMBGPS:  ' + str((IP_EMB, PUERTO_EMBGPS))   )                       
                          sOut.send(recibido)
                          if(tramasLogeadas < 5):
                               log("Enviada trama de GPS a Embarcado " + recibido.decode("utf-8"))
                                               
                            
                     except:
                          e = sys.exc_info()[0]
                          e1 = sys.exc_info()[1]
                          log("No hay conex con el GPS: %s - %s" % (e, e1))
                          print("No hay conex con el GPS: %s - %s" % (e, e1))

                     ## Capturar y convertir la fecha y hora:  
                     ahorita = datetime.now()
                     hora = ahorita.strftime("%H%M") + str(ahorita.second)
                     fecha = ahorita.strftime("%d%m%Y")
                 
#####################################
#Configurar y Corregir valores Trama:
#####################################

                     #Corregir los valores que llegan negativos y deben ser positivos:
                     b = b.replace('-',' ')
                                          
                     # Configuracion de la trama: anadir inicio, idLocomotora y final con velocidad, hora, dia y el nmero de caracteres
                     # a los datos recibidos se le quitan dos caracteres del salto de linea:                  
                     b = "$TEL,IL1:" + idLocomotora + "," + b[:len(b)-2] + "SL1:" + (recibido.decode("utf-8"))[ini:fin] + ",HOR:" + hora + ",DIA:" + fecha + ",*"
                     b = b + str(len(b))                     
                     datosEnvio = b.encode("UTF-8")
                     
                     try:
                          if ((ciclo % SEGUNDOS_EMBARCADO) == 0):
                               semb = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # para conex a embarcado
                               semb.connect((IP_EMB, PUERTO_EMB))
                               semb.send(datosEnvio)
                               if(tramasLogeadas < 5):
                                    log("Enviada trama a Embarcado " + datosEnvio.decode("utf-8"))
                               if pruebas:
                                    print("** Enviada trama a Embarcado " +  datosEnvio.decode("utf-8"))
                     except:
                          e = sys.exc_info()[0]
                          e1 = sys.exc_info()[1]
                          print( "Error: %s - %s" % (e, e1))
                          log( "Error en conexión a embarcado: %s - %s" % (e, e1))
                          semb.close()
                          if pruebas:
                             print("conex. EMB cerrada")                               

                     ## Almacenar la trama en la base de datos
                     if ((ciclo % SEGUNDOS_BD) == 0):
                          cont = con.cursor()
                          cont = con.execute("SELECT COUNT(*) FROM datos")
                          if(cont >= (60*60*24*DIAS_BD)):
                               # Borrar la primera guardada si se ha llegado al límite de almacenaje
                                cur = con.execute("SELECT num FROM datos ORDER BY num ASC LIMIT 1")
                                for i in cur:
                                     con.execute("DELETE FROM datos WHERE (num = %s)" % i[0])
                                     con.commit()
                          cur.execute("INSERT INTO datos (datos) VALUES (' %s ')" % b)
                          con.commit()
                     scct.close()

                     try:
                         scct = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # para conex al CCT es UDP                         
                         scct.sendto(b.encode('utf-8'), ("192.168.2.91", PUERTO_CCT))
                         if(tramasLogeadas < 5):
                              log("** Enviada trama a CCT " + b)
                         if pruebas:
                              print("** Enviada trama a CCT " + IP_CCT + ":" + str(PUERTO_CCT) +  " " + b)
                     except:
                          e = sys.exc_info()[1]
                          print( "Error: %s" % e )
##                          cur.execute("INSERT INTO datos (datos) VALUES (' %s ')" % texto.decode("utf-8"))
##                          con.commit()
##                          scct.close()
                          if pruebas:
                               print('conex. CCT cerrada <====> GUARDADA TRAMA')
               

                     texto = ''
                     scct.shutdown
                     scct.close()
                     print("____________________________________________________________________________")
                     if(tramasLogeadas < 5):
                          tramasLogeadas = tramasLogeadas + 1
                          
                     
     except:
          if pruebas:
               e = sys.exc_info()[1]
               print( "<p>Error: %s</p>" % e )
               print("Se ha perdido la comunicac con el Microcontrolador GEIT")
          puertos_disponibles=scan(num_ports=10,pruebas=True)
          if len(puertos_disponibles)!=0:
               for n,nombre in puertos_disponibles:
                    puertoSerie = nombre
                    if pruebas:
                         print ("Arduino localizado en:  %s" % nombre)
                         arduino = serial.Serial(nombre,baudrate=115200)

               
     if pruebas:
          print(" Finalizada lectura del Microcontrolador GEIT.")
semb.close
scct.close
sOut.shutdown
arduino.close()
