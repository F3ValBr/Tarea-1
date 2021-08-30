# Tarea 1 Modelacion y computacion grafica
# Felipe Valdebenito Bravo 20.404.309-4
from typing import NewType
import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy
import grafica.easy_shaders as es
import grafica.basic_shapes as bs
from grafica.gpu_shape import GPUShape, SIZE_IN_BYTES
import sys

__author__ = "Ivan Sipiran"
__license__ = "MIT"

# We will use 32 bits data, so an integer has 4 bytes
# 1 byte = 8 bits
SIZE_IN_BYTES = 4

#########
# se ha añadido este segmento al codigo para evitar errores al final del mismo
# A class to store the application control
class Controller:
    fillPolygon = True

# we will use the global controller as communication with the callback function
controller = Controller()
#########

# esta funcion va a ser utilizada para generar las piezas del tablero
def crear_dama(x,y,r,g,b,radius):
    
    circle = []
    for angle in range(0,360,10):
        circle.extend([x, y, 0.0, r, g, b])
        circle.extend([x+numpy.cos(numpy.radians(angle))*radius, 
                       y+numpy.sin(numpy.radians(angle))*radius, 
                       0.0, r, g, b])
        circle.extend([x+numpy.cos(numpy.radians(angle+10))*radius, 
                       y+numpy.sin(numpy.radians(angle+10))*radius, 
                       0.0, r, g, b])
    
    ##return numpy.array(circle, dtype = numpy.float32) # este es el return original dado en la tarea
    return bs.Shape(circle, range(len(circle))) #se usa este return como forma inmediata de obtener los circulos en el buffer

#-----------------------------------P1------------------------------------------
# P1. Crear funcion que genere la geometria del tablero y retorne un arreglo
# numpy con la geometria y colores del tablero completo.

# se define crear_tablero como una funcion que no recibe nada y retorna un array con los valores para
# generar el tablero en OpenGL. Se comienza con una lista vacia, valores de referencia para desplazarse
# al continuar el codigo y finalmente, una doble iteracion que recorre primero cada fila y despues cada columna.
def crear_tablero():
    tablero = []

    # x e y tienen el siguiente valor dado que se empezara la iteracion desde la posicion inferior izquierda del tablero
    x = -0.8 
    y = -0.8
    z = 0.0 # z es siempre 0.0 al ser 2D

    x_rest = -1.6
    
    # masX y masY serviran para desplazarse entre fila y columna
    masX = 0.2
    masY = 0.2

    # la primera iteracion recorre cada columna del tablero
    for columna in range(8):
        # la segunda recorre cada 2 cuadros en cada fila, ya que dentro de la iteracion se genera
        # un cuadro negro y blanco a la vez, y se permutan las posiciones segun la columna
        for fila in range(4):
            # contrarresto y resto seran usados como valores para permutar entre el negro y blanco
            contrarresto = columna % 2.0
            resto = 1 - contrarresto
            # generacion de los vertices de un cuadro blanco
            tablero.extend([x,        y,        z, resto, resto, resto])
            tablero.extend([x + masX, y,        z, resto, resto, resto])
            tablero.extend([x + masX, y + masY, z, resto, resto, resto])
            tablero.extend([x,        y + masY, z, resto, resto, resto])
            # generacion de los vertices de un cuadro negro
            x += masX
            tablero.extend([x,        y,        z, contrarresto,contrarresto,contrarresto])
            tablero.extend([x + masX, y,        z, contrarresto,contrarresto,contrarresto])
            tablero.extend([x + masX, y + masY, z, contrarresto,contrarresto,contrarresto])
            tablero.extend([x,        y + masY, z, contrarresto,contrarresto,contrarresto])
            x += masX
            fila += 1
        y += masY
        x += x_rest
        columna += 1
    
    return numpy.array(tablero, dtype = numpy.float32)

# se define una funcion auxiliar que no recibe nada y retorna una lista con los indices a usar para definir los vertices de
# cada cuadro del tablero. Se usara para simplificar la tarea de ingresar cada vertice.
def vertices():
    indices = []
    cuadrado = 0
    for i in range(64):
        indices.extend([cuadrado,   cuadrado+1, cuadrado+2])
        indices.extend([cuadrado+2, cuadrado+3, cuadrado  ])
        cuadrado += 4
        i += 1
    return indices
#-----------------------------------P1------------------------------------------


#-----------------------------------P3------------------------------------------
# # P3. Crear 24 damas (12 de cada color) en las posiciones iniciales

# extender_lista crea ubicaciones de las damas en X, tomando una lista y dos valores de posicion
# y retorna la lista actualizada con los valores de posicion añadidos
def extender_lista(lista,pos1,pos2):
    masX = 0.4
    # esta iteracion se repite cuatro veces para ubicar las piezas en cada columna con un cuadro negro
    for fila_n in range(4):
        lista.extend([pos1, pos2])
        pos1 += masX
        fila_n += 1
    return lista

# ubicar_damas no recibe ningun atributo, y retorna dos listas las cuales contienen las posiciones de las piezas
# rojas y las piezas azules. Funciona de forma similar a la funcion crear_tablero, ubicando las piezas en los cuadros negros
def ubicar_damas():
    # listas vacias para almacenar los datos
    pos_tablero_rojas = []
    pos_tablero_azules = []

    # pos_initX y pos_initY declaran la ubicacion de la primera pieza de dama en el tablero
    pos_initX = -0.7
    pos_initY = 0.7

    # masY modifica la posicion segun la fila en el tablero
    masY = -0.2

    # esta primera iteracion sera para construir la lista con las posiciones de las fichas rojas en el tablero
    # la iteracion se repite 3 veces correspondientes a las 3 filas donde se ubican las piezas
    for columna_n in range(3):
        resto_cuadro = (columna_n % 2)
        # junto con resto_cuadro, este condicional alternara las posiciones del primer cuadro negro en cada fila
        if resto_cuadro == 0:
            pos_initX = -0.7
        extender_lista(pos_tablero_rojas, pos_initX, pos_initY)
        pos_initY += masY
        pos_initX += 0.2*(1-resto_cuadro)
        columna_n += 1

    # estas posiciones reestablecen los valores donde se ubica la primera pieza, ahora sobre las azules
    pos_initX = -0.7
    pos_initY = -0.3

    # esta iteracion cumple el mismo rol que la anterior, pero ahora se hace sobre las damas azules
    for columna_q in range(3):
        resto_cuadro = (columna_q % 2)
        pos_initX += 0.2*(1-resto_cuadro)
        if resto_cuadro != 0:
            pos_initX = -0.7
        extender_lista(pos_tablero_azules, pos_initX, pos_initY)
        pos_initY += masY
        columna_q += 1
    return pos_tablero_rojas, pos_tablero_azules

# finalmente, la funcion posicionar_en_tablero recibe dos listas y retorna una nueva lista con valores actualizados, usando
# principalmente la funcion crear_dama para componer los atributos de dicha lista
def posicionar_en_tablero(lista1, lista2):
    piezas_tablero = []
    # radio compondra el tamaño de las damas en el tablero
    radio = 0.07
    # posicionar piezas rojas
    for i in range(len(lista1)):
        if i % 2 == 0:
            piezas_tablero += [crear_dama(lista1[i], lista1[i+1], 1.0, 0.0, 0.0, radio)]
        i += 1
    # posicionar piezas azules
    for j in range(len(lista2)):
        if j % 2 == 0:
            piezas_tablero += [crear_dama(lista2[j], lista2[j+1], 0.0, 0.0, 1.0, radio)]
        j += 1    
    return piezas_tablero
#-----------------------------------P3------------------------------------------

if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        glfw.set_window_should_close(window, True)

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Tarea 1", None, None)

    if not window:
        glfw.terminate()
        glfw.set_window_should_close(window, True)

    glfw.make_context_current(window)

    # dama = crear_dama(-0.7, 0.7, 1.0, 0.0, 0.0, 0.05) # parte del codigo inicial usado como ejemplo

    # Defining shaders for our pipeline
    vertex_shader = """
    #version 330
    in vec3 position;
    in vec3 color;

    out vec3 newColor;
    void main()
    {
        gl_Position = vec4(position, 1.0f);
        newColor = color;
    }
    """

    fragment_shader = """
    #version 330
    in vec3 newColor;

    out vec4 outColor;
    void main()
    {
        outColor = vec4(newColor, 1.0f);
    }
    """

    # Binding artificial vertex array object for validation
    VAO = glGenVertexArrays(1)
    glBindVertexArray(VAO)

    # Assembling the shader program (pipeline) with both shaders
    shaderProgram = OpenGL.GL.shaders.compileProgram(
        OpenGL.GL.shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
        OpenGL.GL.shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER))

    #-----------------------------------P2------------------------------------------
    # P2. Dibujar el tablero implementando correctamente sus buffers en el GPU y
    # dibujandolo con OpenGL

    # El codigo a continuacion sigue el esquema basico enseñado en catedra y en auxiliar para formar los shaders
    # que compondran la figura final, usando principalmente las funciones crear_tablero y vertices

    vertexData = crear_tablero()
    indices = numpy.array(vertices())
    size = len(indices)
    
    vaoTabla = glGenVertexArrays(1)
    vboTabla = glGenBuffers(1)
    eboTabla = glGenBuffers(1)

    glBindVertexArray(vaoTabla)
    glBindBuffer(GL_ARRAY_BUFFER, vboTabla)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, eboTabla)

    position1 = glGetAttribLocation(shaderProgram, "position")
    glVertexAttribPointer(position1, 3, GL_FLOAT, GL_FALSE, 6 * SIZE_IN_BYTES, ctypes.c_void_p(0))
    glEnableVertexAttribArray(position1)
    
    color1 = glGetAttribLocation(shaderProgram, "color")
    glVertexAttribPointer(color1, 3, GL_FLOAT, GL_FALSE, 6 * SIZE_IN_BYTES, ctypes.c_void_p(3 * SIZE_IN_BYTES))
    glEnableVertexAttribArray(color1)

    # unbinding current vao
    glBindVertexArray(0)

    glBindBuffer(GL_ARRAY_BUFFER, vboTabla)
    glBufferData(GL_ARRAY_BUFFER, len(vertexData) * SIZE_IN_BYTES, vertexData, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, eboTabla)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * SIZE_IN_BYTES, indices, GL_STATIC_DRAW)

    #-----------------------------------P2------------------------------------------

    #-----------------------------------P4------------------------------------------
    # P4. Dibujar las damas implementando correctamente sus buffers en el GPU y dibujandolas
    # con OpenGL

    # Al igual que la P2, se sigue el esquema basico mostrado en catedra y en auxiliar. Lamentablemente
    # en principio este es el codigo funcional, diferenciando cada pieza del tablero de damas como un shader unico cada uno,
    # por lo que el codigo queda engorroso como se muestra abajo como una serie de repeticiones.
    # Para simplificar el codigo lo mas posible, se hizo uso de las librerias otorgadas en el curso

    pipeline = es.SimpleShaderProgram()

    piezas_rojas = ubicar_damas()[0]
    piezas_azules = ubicar_damas()[1]

    piezasShape0 = posicionar_en_tablero(piezas_rojas, piezas_azules)[0]
    gpuPiezas0 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas0)
    gpuPiezas0.fillBuffers(piezasShape0.vertices, piezasShape0.indices, GL_STATIC_DRAW)

    piezasShape1 = posicionar_en_tablero(piezas_rojas, piezas_azules)[1]
    gpuPiezas1 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas1)
    gpuPiezas1.fillBuffers(piezasShape1.vertices, piezasShape1.indices, GL_STATIC_DRAW)

    piezasShape2 = posicionar_en_tablero(piezas_rojas, piezas_azules)[2]
    gpuPiezas2 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas2)
    gpuPiezas2.fillBuffers(piezasShape2.vertices, piezasShape2.indices, GL_STATIC_DRAW)

    piezasShape3 = posicionar_en_tablero(piezas_rojas, piezas_azules)[3]
    gpuPiezas3 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas3)
    gpuPiezas3.fillBuffers(piezasShape3.vertices, piezasShape3.indices, GL_STATIC_DRAW)

    piezasShape4 = posicionar_en_tablero(piezas_rojas, piezas_azules)[4]
    gpuPiezas4 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas4)
    gpuPiezas4.fillBuffers(piezasShape4.vertices, piezasShape4.indices, GL_STATIC_DRAW)

    piezasShape5 = posicionar_en_tablero(piezas_rojas, piezas_azules)[5]
    gpuPiezas5 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas5)
    gpuPiezas5.fillBuffers(piezasShape5.vertices, piezasShape5.indices, GL_STATIC_DRAW)

    piezasShape6 = posicionar_en_tablero(piezas_rojas, piezas_azules)[6]
    gpuPiezas6 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas6)
    gpuPiezas6.fillBuffers(piezasShape6.vertices, piezasShape6.indices, GL_STATIC_DRAW)

    piezasShape7 = posicionar_en_tablero(piezas_rojas, piezas_azules)[7]
    gpuPiezas7 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas7)
    gpuPiezas7.fillBuffers(piezasShape7.vertices, piezasShape7.indices, GL_STATIC_DRAW)

    piezasShape8 = posicionar_en_tablero(piezas_rojas, piezas_azules)[8]
    gpuPiezas8 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas8)
    gpuPiezas8.fillBuffers(piezasShape8.vertices, piezasShape8.indices, GL_STATIC_DRAW)

    piezasShape9 = posicionar_en_tablero(piezas_rojas, piezas_azules)[9]
    gpuPiezas9 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas9)
    gpuPiezas9.fillBuffers(piezasShape9.vertices, piezasShape9.indices, GL_STATIC_DRAW)

    piezasShape10 = posicionar_en_tablero(piezas_rojas, piezas_azules)[10]
    gpuPiezas10 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas10)
    gpuPiezas10.fillBuffers(piezasShape10.vertices, piezasShape10.indices, GL_STATIC_DRAW)

    piezasShape11 = posicionar_en_tablero(piezas_rojas, piezas_azules)[11]
    gpuPiezas11 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas11)
    gpuPiezas11.fillBuffers(piezasShape11.vertices, piezasShape11.indices, GL_STATIC_DRAW)

    piezasShape12 = posicionar_en_tablero(piezas_rojas, piezas_azules)[12]
    gpuPiezas12 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas12)
    gpuPiezas12.fillBuffers(piezasShape12.vertices, piezasShape12.indices, GL_STATIC_DRAW)

    piezasShape13 = posicionar_en_tablero(piezas_rojas, piezas_azules)[13]
    gpuPiezas13 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas13)
    gpuPiezas13.fillBuffers(piezasShape13.vertices, piezasShape13.indices, GL_STATIC_DRAW)

    piezasShape14 = posicionar_en_tablero(piezas_rojas, piezas_azules)[14]
    gpuPiezas14 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas14)
    gpuPiezas14.fillBuffers(piezasShape14.vertices, piezasShape14.indices, GL_STATIC_DRAW)

    piezasShape15 = posicionar_en_tablero(piezas_rojas, piezas_azules)[15]
    gpuPiezas15 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas15)
    gpuPiezas15.fillBuffers(piezasShape15.vertices, piezasShape15.indices, GL_STATIC_DRAW)

    piezasShape16 = posicionar_en_tablero(piezas_rojas, piezas_azules)[16]
    gpuPiezas16 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas16)
    gpuPiezas16.fillBuffers(piezasShape16.vertices, piezasShape16.indices, GL_STATIC_DRAW)

    piezasShape17 = posicionar_en_tablero(piezas_rojas, piezas_azules)[17]
    gpuPiezas17 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas17)
    gpuPiezas17.fillBuffers(piezasShape17.vertices, piezasShape17.indices, GL_STATIC_DRAW)

    piezasShape18 = posicionar_en_tablero(piezas_rojas, piezas_azules)[18]
    gpuPiezas18 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas18)
    gpuPiezas18.fillBuffers(piezasShape18.vertices, piezasShape18.indices, GL_STATIC_DRAW)

    piezasShape19 = posicionar_en_tablero(piezas_rojas, piezas_azules)[19]
    gpuPiezas19 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas19)
    gpuPiezas19.fillBuffers(piezasShape19.vertices, piezasShape19.indices, GL_STATIC_DRAW)

    piezasShape20 = posicionar_en_tablero(piezas_rojas, piezas_azules)[20]
    gpuPiezas20 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas20)
    gpuPiezas20.fillBuffers(piezasShape20.vertices, piezasShape20.indices, GL_STATIC_DRAW)

    piezasShape21 = posicionar_en_tablero(piezas_rojas, piezas_azules)[21]
    gpuPiezas21 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas21)
    gpuPiezas21.fillBuffers(piezasShape21.vertices, piezasShape21.indices, GL_STATIC_DRAW)

    piezasShape22 = posicionar_en_tablero(piezas_rojas, piezas_azules)[22]
    gpuPiezas22 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas22)
    gpuPiezas22.fillBuffers(piezasShape22.vertices, piezasShape22.indices, GL_STATIC_DRAW)

    piezasShape23 = posicionar_en_tablero(piezas_rojas, piezas_azules)[23]
    gpuPiezas23 = GPUShape().initBuffers()
    pipeline.setupVAO(gpuPiezas23)
    gpuPiezas23.fillBuffers(piezasShape23.vertices, piezasShape23.indices, GL_STATIC_DRAW)

    #-----------------------------------P4------------------------------------------

    # Setting up the clear screen color
    glClearColor(0.5,0.5, 0.5, 1.0)

    # Moving our draw to the active color buffer
    glfw.swap_buffers(window)

    # Waiting to close the window
    while not glfw.window_should_close(window):

        # Getting events from GLFW
        glfw.poll_events()

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)
        
        glUseProgram(shaderProgram)

        # Drawing the Quad as specified in the VAO with the active shader program
        glBindVertexArray(vaoTabla)
        glDrawElements(GL_TRIANGLES, size, GL_UNSIGNED_INT, None)

        # esta parte del codigo tambien quedo masiva ya que dibuja cada dama de forma independiente
        pipeline.drawCall(gpuPiezas0)
        pipeline.drawCall(gpuPiezas1)
        pipeline.drawCall(gpuPiezas2)
        pipeline.drawCall(gpuPiezas3)
        pipeline.drawCall(gpuPiezas4)
        pipeline.drawCall(gpuPiezas5)
        pipeline.drawCall(gpuPiezas6)
        pipeline.drawCall(gpuPiezas7)
        pipeline.drawCall(gpuPiezas8)
        pipeline.drawCall(gpuPiezas9)
        pipeline.drawCall(gpuPiezas10)
        pipeline.drawCall(gpuPiezas11)
        pipeline.drawCall(gpuPiezas12)
        pipeline.drawCall(gpuPiezas13)
        pipeline.drawCall(gpuPiezas14)
        pipeline.drawCall(gpuPiezas15)
        pipeline.drawCall(gpuPiezas16)
        pipeline.drawCall(gpuPiezas17)
        pipeline.drawCall(gpuPiezas18)
        pipeline.drawCall(gpuPiezas19)
        pipeline.drawCall(gpuPiezas20)
        pipeline.drawCall(gpuPiezas21)
        pipeline.drawCall(gpuPiezas22)
        pipeline.drawCall(gpuPiezas23)

        glBindVertexArray(0)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    # las siguientes lineas limpian la memoria despues de cerrar la ventana donde aparece el tablero
    glDeleteBuffers(1, [eboTabla])
    glDeleteBuffers(1, [vboTabla])
    glDeleteVertexArrays(1, [vaoTabla])
    
    gpuPiezas0.clear()
    gpuPiezas1.clear()
    gpuPiezas2.clear()
    gpuPiezas3.clear()
    gpuPiezas4.clear()
    gpuPiezas5.clear()
    gpuPiezas6.clear()
    gpuPiezas7.clear()
    gpuPiezas8.clear()
    gpuPiezas9.clear()
    gpuPiezas10.clear()
    gpuPiezas11.clear()
    gpuPiezas12.clear()
    gpuPiezas13.clear()
    gpuPiezas14.clear()
    gpuPiezas15.clear()
    gpuPiezas16.clear()
    gpuPiezas17.clear()
    gpuPiezas18.clear()
    gpuPiezas19.clear()
    gpuPiezas20.clear()
    gpuPiezas21.clear()
    gpuPiezas22.clear()
    gpuPiezas23.clear()

    glfw.terminate()