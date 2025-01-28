import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
import vr_led_control  # Import the original code

# OpenGL State
window = None

# Constants
LED_RADIUS = 0.02  # Radius of each LED sphere
RAY_LENGTH = 5.0  # Length of the imaginary ray
FPS = 60  # Frames per second for rendering


# region OpenGL Rendering Functions
def draw_led(position, color):
    """
    Draw an LED as a sphere at the given position with the given color.
    Args:
        position (tuple): (x, y, z) position of the LED.
        color (tuple): (R, G, B) color of the LED (0–1 float values).
    """
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(*position)
    glutSolidSphere(LED_RADIUS, 16, 16)  # Draw a sphere with the given radius
    glPopMatrix()


def draw_ray(origin, direction):
    """
    Draw the imaginary ray from the controller.
    Args:
        origin (tuple): (x, y, z) position of the ray's start.
        direction (numpy array): Direction vector of the ray.
    """
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.0)  # Red for the ray
    glBegin(GL_LINES)
    glVertex3f(*origin)  # Start of the ray
    glVertex3f(
        origin[0] + direction[0] * RAY_LENGTH,
        origin[1] + direction[1] * RAY_LENGTH,
        origin[2] + direction[2] * RAY_LENGTH,
    )  # End of the ray
    glEnd()
    glPopMatrix()


def render_scene():
    """
    Render the OpenGL scene: LEDs and the controller ray.
    """
    global vr_led_control

    # Clear the screen and depth buffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Set the camera position
    gluLookAt(0, 2, 5, 0, 0, 0, 0, 1, 0)  # Eye position, center position, up vector

    # Get the controller's position and direction
    controller_position = vr_led_control.controller_position
    controller_direction = vr_led_control.controller_direction

    # Draw the ray
    draw_ray(controller_position, controller_direction)

    # Draw the LEDs
    for led_index, position in vr_led_control.led_positions.items():
        # Get the LED color and normalize to 0–1
        color = [
            c / 255.0 for c in vr_led_control.led_state[led_index][:3]
        ]  # Normalize RGB to OpenGL scale
        draw_led(position, color)

    # Swap buffers
    glutSwapBuffers()
# endregion


# region OpenGL Initialization
def init_opengl():
    """
    Initialize OpenGL settings.
    """
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark gray background


def resize_window(width, height):
    """
    Handle window resizing.
    Args:
        width (int): New window width.
        height (int): New window height.
    """
    if height == 0:
        height = 1
    aspect_ratio = width / height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, aspect_ratio, 0.1, 100.0)  # 45° FOV, aspect ratio, near, far planes
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
# endregion


# region Main Loop
def main():
    """
    Main function to start the OpenGL rendering loop.
    """
    global window

    # Initialize OpenGL
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(800, 600)  # Window size
    glutInitWindowPosition(100, 100)  # Window position
    window = glutCreateWindow(b"VR LED Renderer")  # Window title

    # Register callbacks
    glutDisplayFunc(render_scene)
    glutIdleFunc(render_scene)  # Redraw when idle
    glutReshapeFunc(resize_window)

    # Initialize OpenGL settings
    init_opengl()

    # Enter the main loop
    glutMainLoop()
# endregion


if __name__ == "__main__":
    main()
