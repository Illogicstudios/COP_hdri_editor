
import random
import hou
from nodesearch import parser
import lighttracking.updateuv as updateuv

X_NAME = "light_positionx"
Y_NAME = "light_positiony"
Z_NAME = "light_positionz"

HDRI_LIGHTS = "hdri_cop_light"
TOGGLE_VALUE = "script_value0"
LIGHT_TYPE = "light::2.0"

def set_node_connection(input_node, output_node, input_name, output_name):
    """
    Set a connection between two nodes.

    Args:
    input_node (hou.VopNode): Node that receive the connection
    output_node (hou.VopNode): Node that send the connection
    input_name (str): Input's label of the output_node
    output_name (str): Output's label of the input_node
    """

    input_index = output_node.inputIndex(input_name)
    output_index = input_node.outputIndex(output_name)

    # Check index validity
    if (input_index < 0 or output_index < 0):
        print(f"Could not connect ({input_node.name()})"
                   + f" to ({output_node.name()})")
        if input_index < 0:
            print(f"Cannot find ({input_name})"
                        + f" index in ({output_node.name()})")
        if output_index < 0:
            print(f"Cannot find ({output_name})"
                        + f" index in ({input_node.name()})")
        return

    # Set the connection as an input to the output node
    output_node.setInput(input_index, input_node, output_index)

def getRandomColor(seed):
    """
    Basic way to generate a random color, might better next time.

    :results: tuple of 3 float between 0 and 1
    """

    random.seed(seed)
    return (random.uniform(0.0, 1.0), 
            random.uniform(0.0, 1.0), 
            random.uniform(0.0, 1.0))

def run(kwargs):
    """
    Script to generate a light node cluster and link lights to 
    HDRI lights.

    :param kwargs: Current context of the HDRI mapping digital asset
    """

    updateuv.setup_callback(kwargs)

    is_enable = True if kwargs[TOGGLE_VALUE] == 'on' else False

    # Fetch null node HDRI_LIGHT
    mapping_node = kwargs['node']

    if not mapping_node:
        return

    light_name = f"{HDRI_LIGHTS}_{mapping_node.name()}"
    matcher = parser.parse_query(light_name)
    stage = hou.node("/stage/")
    light = matcher.nodes(stage)

    # all_lights_matcher = parser.parse_query(HDRI_LIGHTS)
    # all_lights = matcher.nodes(stage)

    light_x = mapping_node.parm(X_NAME)
    light_y = mapping_node.parm(Y_NAME)
    light_z = mapping_node.parm(Z_NAME)

    

    if is_enable:

        # If light is not found we create a new one
        if not light:
            light = stage.createNode(
                node_type_name=LIGHT_TYPE, node_name=light_name)
        else:
            light = light[0]
        
        # Give light the light position from mapping node
        light.parm("tx").set(light_x.eval())
        light.parm("ty").set(light_y.eval())
        light.parm("tz").set(light_z.eval())

        # Reference light transform as a reference 
        # of light position in mapping node
        light_x.setExpression(f'ch("{light.parm("tx").path()}")')
        light_y.setExpression(f'ch("{light.parm("ty").path()}")')
        light_z.setExpression(f'ch("{light.parm("tz").path()}")')


        # Set light node color randomly based on his name
        light_node_color = getRandomColor(light_name)
        color = hou.Color(light_node_color)
        light.setColor(color)


        # Select light node and adjust position in network view

        # TODO There is problem if we select the light without being in the panel raising
        # a lot of errors, it's seems related to the way houdini handle his viewer state 
        # and mess up the light handle one.

        # Set light node position close the hdri copnet
        hdri_cop_net_node = mapping_node.parent()
        if (hdri_cop_net_node):
            offset = hou.Vector2(0, -1)
            parent_position = hdri_cop_net_node.position()

            light.setPosition(parent_position + offset)

            scene_viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)

            if scene_viewer:
                scene_viewer.setPwd(stage)
            light.setSelected(True, clear_all_selected=True) 

        else:
            # Fallback if for some unknown reasons we cannot select the hdri copnet

            light.moveToGoodPosition()

    else:
        
        if not light:
            return
        
        light_x.deleteAllKeyframes()
        light_y.deleteAllKeyframes()
        light_z.deleteAllKeyframes()

        light = light[0]
        light.destroy()
