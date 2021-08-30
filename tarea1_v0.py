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
    
    ##return numpy.array(circle, dtype = numpy.float32)
    return bs.Shape(circle, range(len(circle)))

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
            piezas_tablero += [crear_dama(lista1[i], lista1[i+1], 1.0, 0.0, 0.0, radio)]
        i += 1
    for j in range(len(lista2)):
        if j % 2 == 0:
            piezas_tablero += [crear_dama(lista2[j], lista2[j+1], 0.0, 0.0, 1.0, radio)]
        j += 1    
    #return bs.Shape(piezas_tablero, range(len(piezas_tablero)))
    return piezas_tablero

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

    dama = crear_dama(-0.7, 0.7, 1.0, 0.0, 0.0, 0.05)

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

    pipeline = es.SimpleShaderProgram()

    piezas_rojas = ubicar_damas()[0]
    piezas_azules = ubicar_damas()[1]

    ##piezasShape = posicionar_en_tablero(piezas_rojas, piezas_azules)
        ##piezasShape = dama
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

        #glBindVertexArray(VAO)
        #glDrawArrays(GL_TRIANGLES, 0, int(len(dama)/6))

        #glBindVertexArray(0)
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

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