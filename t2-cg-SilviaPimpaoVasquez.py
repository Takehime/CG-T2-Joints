# -*- coding: utf-8 -*-
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

##Global list for polygons.
polygons_list = []
##Global list for joints.
joints_list = []
##Keeps reference to polygon being moved or rotated.
selected_polygon = None

##Starter value for polygons ids.
poly_id = 0
##Starter value for joints ids.
joint_id = 0

##States of the program.
moving_poly = False
creating_poly = False

##Mouse position on last frame.
last_mouse_pos = None
##Mouse position on current frame.
curr_mouse_pos = None

##Class that keeps the coordinates of a point.
class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

##Class that keeps points of a line.
class line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return "p1 (" + str(self.p1.x) + ", " + str(self.p1.y) + "), " + "p2 (" + str(self.p2.x) + ", " + str(self.p2.y) + "), "

##Class that keeps information about a polygon.
class polygon:
    def __init__(self, listOfPoints, color):
        global poly_id        
        self.points = listOfPoints
        self.color = color
        self.parent = None
        self.ancestor = self
        self.child = []
        self.joint_to_father = None
        self.id = poly_id
        poly_id = poly_id + 1

    def __str__(self):
        return "id: " + str(self.id)

##Class that keeps information about a joint.
class joint:
    def __init__(self, x, y, parent, child):
        global joint_id
        self.x = x
        self.y = y
        self.parent = parent
        self.child = child
        self.id = joint_id
        joint_id = joint_id + 1

    def __str__(self):
        return "id: " + str(self.id)

##Convert from mouse coordinates to Ortho2D coordinates.
#@param x, y X and Y coordinates to be converted.
def convertCoords(x, y):
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    x = x/float(width)
    y = y/float(-height) +1
    return x, y

##Check if a point is inside any polygon on screen and updates selected polygon.
def checkIfPointInAnyPolygon(point):
    global selected_polygon
    in_any_polygon = False
    for p in reversed(polygons_list):
        in_any_polygon = pointInPolygon(point, p)
        if in_any_polygon == True:
            selected_polygon = p
            return in_any_polygon
    return in_any_polygon


##Check if a point is inside exactly two polygons on screen and updates selected polygon.
def checkIfPointInTwoPolygons(point):
    polys_found = []
    for p in polygons_list:
        in_any_polygon = pointInPolygon(point, p)
        if in_any_polygon == True:
            polys_found.append(p)
            if polys_found == 2:
                break
    return polys_found

##Reset mouse positions.
def resetMouseCoords():
    global last_mouse_pos, curr_mouse_pos
    last_mouse_pos = None
    curr_mouse_pos = None

##Set the current state to moving polygon on screen.
def enterMovePolyMode():
    global moving_poly
    moving_poly = True

##Deactivate the state of moving polygon on screen.
def leaveMovePolyMode():
    global moving_poly
    moving_poly = False


##List that holds points of a yet not completed polygon.
polygon_points = []
##List that holds line segments of a yet not completed polygon.
polygon_lines = []

last_point = None
##Mouse callback function.
#Checks if mouse left button was pressed.
#Creates a line with mouse coordinates when left button is released.
#@param button Pressed button.
#@param state State of the button.
#@param x X coord of mouse.
#@param y Y coord of mouse.
def mouse(button, state, x, y):
    global polygon_lines, polygon_points, last_point, polygons_list, creating_poly
    resetMouseCoords()
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if creating_poly == False:
                new_x, new_y = convertCoords(x, y)
                p = point(new_x, new_y)
                in_poly = checkIfPointInAnyPolygon(p)

                if in_poly == True:
                    enterMovePolyMode()
                    last_point = None
                else:
                    creating_poly = True

        elif state == GLUT_UP:
            if moving_poly == True:
                leaveMovePolyMode()
            elif creating_poly == True:
                createPolyMode(x, y)

    elif button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            new_x, new_y = convertCoords(x, y)
            p = point(new_x, new_y)

            joint = jointAlreadyExists(new_x, new_y)

            if joint != None:
                removeJoint(new_x, new_y, joint)
            else:
                polys_to_joint = checkIfPointInTwoPolygons(p)
                if len(polys_to_joint) == 2:
                    createJoint(p, polys_to_joint)

##Keyboard callback function.
def keyboard(key, x, y):
    if key == 'z':
        if creating_poly == True:
            endPolyCreation()
    elif key == 'c':
        clearScreen()

##Clear screen and reset default values.
def clearScreen():
    global polygons_list, joints_list, selected_polygon
    endPolyCreation()
    resetMouseCoords()
    polygons_list = []
    joints_list = []
    selected_polygon = None

##Resets all temporary values responsables for creating a new polygon.
def endPolyCreation():
    global polygon_lines, polygon_points, last_point, creating_poly
    del polygon_points[:]
    del polygon_lines[:]
    last_point = None
    creating_poly = False

##Checks if there is an existing joint on the given coordinates.
def jointAlreadyExists(x, y):
    global joints_list
    minx = x - 0.01
    maxx = x + 0.01
    miny = y - 0.01
    maxy = y + 0.01

    for j in joints_list:
        if j.x > minx and j.x < maxx and j.y > miny and j.y < maxy:
            return j
    return None

##Remove a joint from a given location.
def removeJoint(x, y, j):
    global joints_list
    joints_list.remove(j)
    pai = j.parent
    filho = j.child
    pai.child.remove(filho)
    filho.parent = None
    filho.ancestor = filho
    pai.ancestor = pai

##Sets a new ancestor entity to a polygon.
def setNewAncestor(anc, poly):
    if len(poly.child) == 0:
        return
    for c in poly.child:
        c.ancestor = anc
        setNewAncestor(anc, c)

##Create a new joint between two polygons.
#@param p Point of joint.
#@param polys_to_joint List of two polygons to be jointed. 
def createJoint(p, polys_to_joint):
    pai = polys_to_joint[0]
    filho = polys_to_joint[1]

    if pai.ancestor == filho.ancestor:
        return

    if filho.parent != None and pai.parent != None:
        return
    
    if filho.parent != None and pai.parent == None:
        pai = polys_to_joint[1]
        filho = polys_to_joint[0]
    
    new_joint = joint(p.x, p.y, pai, filho)
    joints_list.append(new_joint)
    pai.child.append(filho)
    filho.joint_to_father = new_joint
    filho.parent = pai
    filho.ancestor = pai.ancestor
    setNewAncestor(pai.ancestor, pai)

def invertFamilyOfPolygons(filho, pai, joint):
    pai_antigo = filho.parent
    joint_antigo = filho.joint_to_father
    filho_antigo = filho

    while pai_antigo != None:
        pai_antigo = filho.parent
        joint_antigo = filho.joint_to_father

        filho.parent = pai
        filho.ancestor = pai.ancestor

        filho.joint_to_father = joint

        if pai_antigo != None:
            filho.child.append(pai_antigo)

        filho_antigo = filho
        filho = pai_antigo
        pai = filho_antigo

        joint = joint_antigo

##Handles creation of a new polygon.
#Creates a new polygon when it detects an intersection between first and last line segments.
def createPolyMode(x, y):
    global polygon_lines, polygon_points, last_point, polygons_list, creating_poly
    new_x, new_y = convertCoords(x, y)
    p = point(new_x, new_y)

    if last_point != None:
        new_segment = line(last_point, p)
        polygon_lines.append(new_segment)
    polygon_points.append(p)
    last_point = p

    if len(polygon_lines) > 2:
        first_last_seg = [polygon_lines[0], polygon_lines[len(polygon_lines) -1]]
        intersec = findIntersections(first_last_seg)

        if intersec != None: #poligono fechado
            polygon_points[len(polygon_points) - 1] = intersec

            list_of_points = []
            for i in range(1, len(polygon_points)):
                list_of_points.append(polygon_points[i])

            color = [random.random(), random.random(), random.random()]
            new_poly = polygon(list_of_points, color)
            polygons_list.append(new_poly)
            endPolyCreation()

##Calculates if there is an intersection between a point and a given polygon.
def pointInPolygon(point, poly):
    x = point.x
    y = point.y
    inside = False
    lst = poly.points
    for i in range(len(lst)):
        xi = poly.points[i].x
        yi = poly.points[i].y
        xj = poly.points[i-1].x
        yj = poly.points[i-1].y
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
    return inside

last_mouse_pos = None
curr_mouse_pos = None
##Motion callback function.
def motion(x, y):
    global last_mouse_pos, curr_mouse_pos
    last_mouse_pos = curr_mouse_pos
    new_x, new_y = convertCoords(x, y)
    curr_mouse_pos = point(new_x, new_y)
    if moving_poly == True:
        definePolyMotion(x, y)

##Defines what kind of movement the selected polygon shall do.
def definePolyMotion(x, y):
    global selected_polygon
    if selected_polygon.parent == None:
        translation(selected_polygon)
    else:
        rotation(selected_polygon.joint_to_father, selected_polygon)
        
##Rotates a polygon in relation to a joint point.
#@param joint A joint, to rotate in relation to it.
#@param polygon Polygon to be rotated.
def rotation(joint, polygon):
    global last_mouse_pos, curr_mouse_pos
    if last_mouse_pos != None and curr_mouse_pos != None:
        x1 = joint.x - last_mouse_pos.x
        y1 = joint.y - last_mouse_pos.y
        x2 = joint.x - curr_mouse_pos.x
        y2 = joint.y - curr_mouse_pos.y
        esc_prod = ((x1 * x2) + (y1 * y2))
        mod = math.sqrt(x1*x1 + y1*y1) * math.sqrt(x2*x2 + y2*y2)
        cos = esc_prod / float(mod)
        if cos < - 1 or cos > 1:
            return
        angle = math.acos(cos)
        angle = directionOfRotation(x1, y1, x2, y2) * angle

        for point in polygon.points:
            tx = (math.sin(angle) * joint.y - math.cos(angle) * joint.x + joint.x)
            ty = (math.sin(angle) * joint.x - math.cos(angle) * joint.y + joint.y)
            new_x = (math.cos(angle) * (point.x - joint.x)) - (math.sin(angle) * (point.y - joint.y)) + joint.x
            new_y = (math.sin(angle) * (point.x - joint.x)) + (math.cos(angle) * (point.y - joint.y)) + joint.y
            point.x = new_x
            point.y = new_y

        if polygon.joint_to_father != None:
            x = polygon.joint_to_father.x
            y = polygon.joint_to_father.y
            new_x = (math.cos(angle) * (x - joint.x)) - (math.sin(angle) * (y - joint.y)) + joint.x
            new_y = (math.sin(angle) * (x - joint.x)) + (math.cos(angle) * (y - joint.y)) + joint.y
            polygon.joint_to_father.x = new_x
            polygon.joint_to_father.y = new_y
        
        for c in polygon.child:
            rotation(joint, c)

##Defines if a rotation is clockwise or counterclockwise based on two vectors.
def directionOfRotation(v1x, v1y, v2x, v2y):
    if (v1y * v2x) > (v1x * v2y):
        return -1
    else:
        return 1

##Returns the intersection point of two finite line segments 'pq' and 'rs'. If it doesn't exist, return None.
#Handles division by zero.
#@param p, q First Line Points.
#@param r, s Second Line Points.
def translation(polygon):
    global last_mouse_pos, curr_mouse_pos
    if last_mouse_pos != None and curr_mouse_pos != None:
        t_vector_x = curr_mouse_pos.x - last_mouse_pos.x
        t_vector_y = curr_mouse_pos.y - last_mouse_pos.y
        for point in polygon.points:
            point.x = point.x + t_vector_x
            point.y = point.y + t_vector_y

        if polygon.joint_to_father != None:
            polygon.joint_to_father.x = polygon.joint_to_father.x + t_vector_x
            polygon.joint_to_father.y = polygon.joint_to_father.y + t_vector_y
        
        for c in polygon.child:
            translation(c)

##Iterate through a list of lines to find intersections between them.
def findIntersections(list_of_lines):
    for i in xrange (0, len(list_of_lines)):
        for j in xrange (i + 1, len(list_of_lines)):
            p = point(list_of_lines[i].p1.x, list_of_lines[i].p1.y)
            q = point(list_of_lines[i].p2.x, list_of_lines[i].p2.y)
            r = point(list_of_lines[j].p1.x, list_of_lines[j].p1.y)
            s = point(list_of_lines[j].p2.x, list_of_lines[j].p2.y)
            return getIntersection(p, q, r, s)

##Returns the intersection point of two finite line segments 'pq' and 'rs'. If it doesn't exist, return None.
#Handles division by zero.
#@param p, q First Line Points.
#@param r, s Second Line Points.
def getIntersection(p, q, r, s):
    s1_x = q.x - p.x
    s1_y = q.y - p.y
    s2_x = s.x - r.x
    s2_y = s.y - r.y
    s3_x = p.x - r.x
    s3_y = p.y - r.y

    if (-s2_x * s1_y + s1_x * s2_y) == 0:
        return None

    s = (-s1_y * s3_x + s1_x * s3_y) / (-s2_x * s1_y + s1_x * s2_y)
    t = ( s2_x * s3_y - s2_y * s3_x) / (-s2_x * s1_y + s1_x * s2_y)

    if (s >= 0 and s <= 1 and t >= 0 and t <= 1):
        x= p.x + (t * s1_x)
        y = p.y + (t * s1_y)
        intersection = point(x, y)
        return intersection

##Class draws a line on screen.
def drawLine(l):
    glColor3f(0, 0, 0)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(l.p1.x, l.p1.y)
    glVertex2f(l.p2.x, l.p2.y)
    glEnd()

##Class draws a point on screen.
def drawPoint(c):
    glEnable(GL_POINT_SMOOTH)
    glColor3f(0, 0, 0)
    glPointSize(10.0)
    glBegin(GL_POINTS)
    glVertex2f(c.x, c.y)
    glEnd()

##Class draws a polygon on screen.
def drawPolygon(poligon):
    glLineWidth(2.5)
    glColor3f(poligon.color[0], poligon.color[1], poligon.color[2])
    tess = gluNewTess()
    gluTessCallback(tess, GLU_BEGIN, glBegin)
    gluTessCallback(tess, GLU_VERTEX, glVertex3dv)
    gluTessCallback(tess, GLU_END, glEnd)
    gluBeginPolygon(tess)

    for p in poligon.points:
        gluTessVertex(tess, [p.x, p.y, 0], [p.x, p.y, 0])
    gluEndPolygon(tess)
    gluDeleteTess(tess)

##Display callback function
def display():
    glClearColor(0.9, 0.9, 0.9, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    for polygon in polygons_list:
        drawPolygon(polygon)
        for joint in joints_list:
            if joint.parent.id == polygon.id or joint.child.id == polygon.id:
                drawPoint(joint)
            
    for l in polygon_lines:
        drawLine(l)
        
    glutSwapBuffers()

##Reshape callback function
def reshape(w, h):
    glViewport (0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, 1.0, 0.0, 1.0)

##Main
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
glutInitWindowSize(600, 600)
glutInitWindowPosition(0, 0)
window = glutCreateWindow("CG - Trabalho 2")
glutDisplayFunc(display)
glutIdleFunc(display)
glutReshapeFunc(reshape)
glutMouseFunc(mouse)
glutMotionFunc(motion)
glutKeyboardFunc(keyboard)
print "***"
print "Trabalho 2 da Disciplina Computacao Grafica - UFRJ 2017.2"
print "Aluna: Silvia Pimpao Vasquez. DRE: 115094560"
print "***"
glutMainLoop()