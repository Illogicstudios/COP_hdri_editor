
import hou
import time
import numpy as np
import math

X_NAME = "light_positionx"
Y_NAME = "light_positiony"
Z_NAME = "light_positionz"

U_NAME = "uv_positionx"
V_NAME = "uv_positiony"

DEBUG = False

def updateUV(hdri_mapping_node):
    
    """
    Update UV coordinates channel from light position channel.

    :param node: Hdri mapping node to update
    """

    if DEBUG:
        print("Updating UV...")
        start = time.process_time_ns()

    # Retrieve light position parameters
    x = hdri_mapping_node.parm(X_NAME)
    y = hdri_mapping_node.parm(Y_NAME)
    z = hdri_mapping_node.parm(Z_NAME)

    # Retrieve UV coordinate parameters
    u = hdri_mapping_node.parm(U_NAME)
    v = hdri_mapping_node.parm(V_NAME)

    if x is None or y is None or z is None:
        print("Could not retrieve light position")
        return
    
    if u is None or v is None:
        print("Could not retrieve UV channel")
        return
    
    light_position = np.array([x.eval(), y.eval(), z.eval()], dtype=float)
    
    uv = computeUV(light_position)

    u.set(uv[0])
    v.set(uv[1])

    if DEBUG:
        time_ns = time.process_time_ns() - start
        time_sec = time_ns / 1000000000
        
        print(f"Light position = ({light_position[0]}, {light_position[1]}, {light_position[2]})")
        print(f"UV = ({uv[0]}, {uv[1]})")
        print(f"Time taken : {time_sec} s | {time_ns} ns")

def updateLightPosition(hdri_mapping_node):
    """
    Update light position from UV coordinate while keeping the same
    norm.

    :param node: Hdri mapping node to update
    """
    if DEBUG:
        print("Updating UV...")
        start = time.process_time_ns()

    # Retrieve light position parameters
    x = hdri_mapping_node.parm(X_NAME)
    y = hdri_mapping_node.parm(Y_NAME)
    z = hdri_mapping_node.parm(Z_NAME)

    # Retrieve UV coordinate parameters
    u = hdri_mapping_node.parm(U_NAME)
    v = hdri_mapping_node.parm(V_NAME)

    if x is None or y is None or z is None:
        print("Could not retrieve light position")
        return
    
    if u is None or v is None:
        print("Could not retrieve UV channel")
        return

    uv = np.array([u.eval(), v.eval()], dtype=float)
    light_position = np.array([x.eval(), y.eval(), z.eval()], dtype=float)
    
    light_position = computeLightPosition(uv, light_position)

    x.set(light_position[0])
    y.set(light_position[1])
    z.set(light_position[2])

    if DEBUG:
        time_ns = time.process_time_ns() - start
        time_sec = time_ns / 1000000000
        
        print(f"Light position = ({light_position[0]}, {light_position[1]}, {light_position[2]})")
        print(f"UV = ({uv[0]}, {uv[1]})")
        print(f"Time taken : {time_sec} s | {time_ns} ns")

def computeUV(light_position: np.ndarray):
    """
    Compute UV coordinates from 3D coordinates over a sphere.

    Note: The sphere has a radius of 1 and is centered in (0, 0, 0)

    :param light_position: A 3D vector store in a numpy array
    :returns vector: A 2D vector with UV coordinates or None if wrong input
    """

    if light_position.size != 3 or light_position.ndim != 1:
        return None

    normalized_light_position = normalize(light_position)

    phi = math.atan2(
        normalized_light_position[2],
        normalized_light_position[0])
    theta = math.asin(max(-1, min(1, normalized_light_position[1])))
    
    phi += math.pi * -0.5
    
    u = phi / (2.0*math.pi) + 0.5
    v = 0.5 - (theta/math.pi)
    v = 1 - v

    return np.array([u, v])

def computeLightPosition(uv_coordinates: np.ndarray, light_position: np.ndarray):
    """
    Compute light position from UV coordinates on sphere while keeping
    the same distance.

    Note: The sphere has a radius of 1 and is centered in (0, 0, 0)

    :param uv_coordinates: A 2D vector with current UV coordinates
    :returns vector: A 3D vector with the new light position
    """

    if uv_coordinates.size != 2 or uv_coordinates.ndim != 1:
        return None
    if light_position.size != 3 or light_position.ndim != 1:
        return None

    distance = np.linalg.norm(light_position)

    theta = 2.0 * math.pi * (uv_coordinates[0] - 0.25)
    phi = math.pi * (0.5 - (1 - uv_coordinates[1]))

    x = distance * math.cos(phi) * math.cos(theta)
    y = distance * math.sin(phi)
    z = distance * math.cos(phi) * math.sin(theta)

    return np.array([x, y, z])

def normalize(vector: np.ndarray):
    """
    Normalize a vector in a numpy array.
    
    :param vector: A n-D vector hold in a numpy array
    :returns: The same vector normalized
    """

    vector = np.asarray(vector)

    norm = float(np.linalg.norm(vector))
    if norm == 0: 
       return vector

    normalized_vector = vector / norm

    return normalized_vector
    
def on_light_position_change(**kwargs):
    """
    Callback when a light position changes.
    """
    
    if kwargs is None:
        return
    
    parm = kwargs['parm_tuple']
    node = kwargs['node']

    if parm is None or node is None:
        return

    if not len(parm):
        return 
    
    parm = parm[0]

    if node.userData("callback_in_progress") == "1":
        return

    if ("light_position" in parm.name()):
        try:
            node.setUserData("callback_in_progress", "1")
            updateUV(node)
        finally:
            node.setUserData("callback_in_progress", "0")


def on_uv_coordinates_change(**kwargs):
    """
    Callback when a uv coordinates changes.
    """
    
    if kwargs is None:
        return
    
    parm = kwargs['parm_tuple']
    node = kwargs['node']

    if parm is None or node is None:
        return

    if not len(parm):
        return
    
    parm = parm[0]

    if node.userData("callback_in_progress") == "1":
        return

    if ("uv_position" in parm.name()):
        try:
            node.setUserData("callback_in_progress", "1")
            updateLightPosition(node)
        finally:
            node.setUserData("callback_in_progress", "0")

def setup_callback(kwargs):
    """
    A method supposed to be called when a subnetwork is created 
    or updated to add a callback on light position that update UVs.

    :param kwargs: Node context
    """

    mapping_node = kwargs["node"]

    mapping_node.removeAllEventCallbacks()

    mapping_node.setUserData("callback_in_progress", "0")
    
    mapping_node.addEventCallback(
        (hou.nodeEventType.ParmTupleChanged, ),
        on_light_position_change
    )
    
    mapping_node.addEventCallback(
        (hou.nodeEventType.ParmTupleChanged, ),
        on_uv_coordinates_change
    )
    