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
# A class to store the application control
class Controller:
    fillPolygon = True

# we will use the global controller as communication with the callback function
controller = Controller()
#########

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
    
    return numpy.array(circle, dtype = numpy.float32)

#########
# 1. Crear funcion que genere la geometria del tablero y retorne un arreglo
# numpy con la geometria y colores del tablero completo.
def crear_tablero():
    tablero = []

    x = -0.8
    y = -0.8
    z = 0.0 # z es siempre 0.0 al ser 2D

    x_rest = -1.6
    
    masX = 0.2
    masY = 0.2

    for columna in range(8):
        for fila in range(4):
            contrarresto = columna % 2.0
            resto = 1 - contrarresto
            # cuadro blanco
            tablero.extend([x,        y,        z, resto, resto, resto])
            tablero.extend([x + masX, y,        z, resto, resto, resto])
            tablero.extend([x + masX, y + masY, z, resto, resto, resto])
            tablero.extend([x,        y + masY, z, resto, resto, resto])
            # cuadro negro
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

def vertices():
    indices = []
    cuadrado = 0
    for i in range(64):
        indices.extend([cuadrado,   cuadrado+1, cuadrado+2])
        indices.extend([cuadrado+2, cuadrado+3, cuadrado  ])
        cuadrado += 4
        i += 1
    return indices
#########
# P2. Dibujar el tablero implementando correctamente sus buffers en el GPU y
# dibujandolo con OpenGL

# P3. Crear 24 damas (12 de cada color) en las posiciones iniciales
# crea ubicaciones de las damas en X
def extender_lista(lista,pos1,pos2):
    masX = 0.4
    for fila_n in range(4):
        lista.extend([pos1, pos2])
        pos1 += masX
        fila_n += 1
    return lista

def ubicar_damas():
    pos_tablero_rojas = []
    pos_tablero_azules = []

    pos_initX = -0.7
    pos_initY = 0.7

    masY = -0.2

    for columna_n in range(3):
        resto_cuadro = (columna_n % 2)
        if resto_cuadro == 0:
            pos_initX = -0.7
        extender_lista(pos_tablero_rojas, pos_initX, pos_initY)
        pos_initY += masY
        pos_initX += 0.2*(1-resto_cuadro)
        columna_n += 1

    pos_initX = -0.7
    pos_initY = -0.3

    for columna_q in range(3):
        resto_cuadro = (columna_q % 2)
        pos_initX += 0.2*(1-resto_cuadro)
        if resto_cuadro != 0:
            pos_initX = -0.7
        extender_lista(pos_tablero_azules, pos_initX, pos_initY)
        pos_initY += masY
        columna_q += 1
    return pos_tablero_rojas, pos_tablero_azules

def posicionar_en_tablero(lista1, lista2):
    piezas_tablero = []
    radio = 0.07
    # posicionar piezas rojas
    for i in range(len(lista1)):
        if i % 2 == 0:
            crear_dama(lista1[i], lista[i+1], 1.0, 0.0, 0.0, radio)
        i += 1


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

    dama = crear_dama(0.5,0.0, 0.0, 1.0, 0.0, 0.2)

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

    ########
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

#############    
    #vboDama = glGenBuffers(1)
    
    #glBindBuffer(GL_ARRAY_BUFFER, vboDama)
    #position = glGetAttribLocation(shaderProgram, "position")
    #glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
    #glEnableVertexAttribArray(position)

    #color = glGetAttribLocation(shaderProgram, "color")
    #glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
    #glEnableVertexAttribArray(color)
    
    #glBindVertexArray(0)

    # Each shape must be attached to a Vertex Buffer Object (VBO)
    #glBindBuffer(GL_ARRAY_BUFFER, vboDama)
    #glBufferData(GL_ARRAY_BUFFER, len(dama) * SIZE_IN_BYTES, dama, GL_STATIC_DRAW)
 
    # Telling OpenGL to use our shader program
    ##glUseProgram(shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.5,0.5, 0.5, 1.0)

    #glClear(GL_COLOR_BUFFER_BIT)

    #glBindBuffer(GL_ARRAY_BUFFER, vboDama)
    #position = glGetAttribLocation(shaderProgram, "position")
    #glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
    #glEnableVertexAttribArray(position)

    #color = glGetAttribLocation(shaderProgram, "color")
    #glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
    #glEnableVertexAttribArray(color)

    # It renders a scene using the active shader program (pipeline) and the active VAO (shapes)
    #glDrawArrays(GL_TRIANGLES, 0, int(len(dama)/6))

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

        glBindVertexArray(0)

        #glBindVertexArray(VAO)
        #glDrawArrays(GL_TRIANGLES, 0, int(len(dama)/6))

        #glBindVertexArray(0)
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glDeleteBuffers(1, [eboTabla])
    glDeleteBuffers(1, [vboTabla])
    glDeleteVertexArrays(1, [vaoTabla])

    glfw.terminate()