import hou

BLENDTYPE = "blend"
ADDMODE = 3

CONFIG_NODE_NAME = "config_blend"

def onInputChanged(kwargs):
    """Callback on a multi blend subnetwork which 
    will adjust the number of blend connections.

    Args:
        kwargs (dict): Subnetwork context

    Raises:
        KeyError: Cannot find necessary informations in kwargs
        KeyError: Cannot find input or ouput not in the subnet
    """

    # Check if the context is correct
    if "node" not in kwargs or "input_index" not in kwargs:
        raise KeyError(
            "Missing required keys in kwargs: 'node' or 'input_index'")

    subnet: hou.Node = kwargs["node"]
    input_to_connect = kwargs["input_index"]

    # Parse subnet inputs and outputs and leave if we cant
    inputs_node = None
    outputs_node = None

    for node in subnet.children():
        if node.type().name() == "input":
            inputs_node = node
        if node.type().name() == "output":
            outputs_node = node
        if inputs_node and outputs_node:
            break

    if (inputs_node is None or outputs_node is None):
        raise KeyError("Could not find input or output node")
    
    # Clear already existing connection
    for connection in inputs_node.outputConnections():
        if connection.outputIndex() == input_to_connect:
            connection.outputNode().setInput(
                connection.inputIndex(), None)
            break

    ## Parse all blend nodes
    # and parse 3 types of blend node:
    # 1 - Blend nodes with an input in fg or bg free
    # 2 - Blend node connected to the final output
    # 3 - Blend node named config_node
    blend_nodes = []
    blend_nodes_with_free_input = []
    blend_node_connected_to_output  = None
    config_node = None

    for child in subnet.children():
        if (child.type().name() == BLENDTYPE):
            
            if(child.name() == CONFIG_NODE_NAME):
                config_node = child
                continue

            blend_nodes.append(child)

            # Get every valid input and output
            child_inputs = [input for input in child.inputs()
                             if input is not None]
            child_outputs = [output for output in child.outputs()
                              if output is not None]
            if len(child_inputs) == 1:
                blend_nodes_with_free_input.append(child)
            if len(child_outputs) == 1:
                if (child_outputs[0].type().name() == "output"):
                    blend_node_connected_to_output  = child

    # Clean useless blend nodes
    cleanBlend(blend_nodes)

    # Check if the input changed was a new connection
    connecting = subnet.input(input_to_connect) is not None

    # If an input has been disconnect, we need to clean the subnetwork
    if not connecting:
        # Rewire every node that have only one connection and
        # if that's connection input is fg
        for blend_node in blend_nodes:
            blend_node_inputs = [input for input in blend_node.inputs()
                                if input is not None]
            
            if len(blend_node_inputs) == 1:
                connection = blend_node.inputConnections()[0]
                # If the only connection of the node is on fg
                # Then swap it to bg
                if connection.inputIndex() == 1:
                    blend_node.setInput(0,
                                    connection.inputNode(),
                                    connection.outputIndex())
                    blend_node.setInput(1, None)

        updateLayout(subnet, inputs_node, config_node)
        return
    
    # Try to connect to a node with a free input
    if blend_nodes_with_free_input:
        for input_index, connectors in enumerate(
            blend_nodes_with_free_input[0].inputConnectors()):
            if len(connectors) == 0 and input_index != 2:
                blend_nodes_with_free_input[0].setInput(
                    input_index, inputs_node, input_to_connect)
                break
    # Else add a new blend node
    else:
        if blend_node_connected_to_output is not None:

            outputs_node.setInput(0, None)

            new_blend = createBlend(subnet, config_node)

            new_blend.setInput(0, blend_node_connected_to_output , 0)
            new_blend.setInput(1, inputs_node, input_to_connect)
            outputs_node.setInput(0, new_blend, 0)

        # If there is no blend node with the output node as output
        # we need output our new blend here
        else:
            new_blend = createBlend(subnet, config_node)
            new_blend.setInput(0, inputs_node, 0)
            subnet.subnetOutputs()[0].setInput(0, new_blend, 0)

            for blend in blend_nodes:
                if not len(blend.outputs()):
                    blend_node_connected_to_output = blend

            if blend_node_connected_to_output  is not None:
                new_blend.setInput(1, blend_node_connected_to_output)
    
    updateLayout(subnet, inputs_node, config_node)
   

def updateLayout(
        subnet: hou.Node, input_nodes: hou.Node=None,
        config_node: hou.Node=None):
    """Layout nodes in the subnet nicely.

    Args:
        subnet (hou.Node): Multi blend subnetwork
        input_nodes (hou.Node, optional): input node of subnet. Defaults to None.
        config_node (hou.Node, optional): Blend node that serve as config node. Defaults to None.
    """
    subnet.layoutChildren()

    if config_node is None or input_nodes is None:
        return

    offset = hou.Vector2(0, -2)
    parent_position = input_nodes.position()

    config_node.setPosition(parent_position + offset)


def cleanBlend(blend_nodes: list):
    """Clean recursively every node that does not have inputs.

    Args:
        blend_nodes (list): List of blend nodes
    """
    to_delete = [blend for blend in blend_nodes if not blend.inputs()]
    while to_delete:
        for blend in to_delete:
            if(blend.name() == CONFIG_NODE_NAME):
                continue
            blend.destroy()
            blend_nodes.remove(blend)
        to_delete = [blend for blend in blend_nodes if not blend.inputs()]


def createBlend(subnet: hou.Node, config_node: hou.Node=None):
    """Create a blend node with a specific context.

    Default: mode set to add

    Optionnaly: Same parameters as config_node
    
    Args:
        subnet (hou.Node): Multi blend subnetwork
        config_node (hou.Node, optional): A blend to copy. Defaults to None.

    Returns:
        hou.Node: Created blend node
    """

    if config_node is None:
        blend = subnet.createNode(node_type_name=BLENDTYPE)
        blend.parm("mode").set(ADDMODE)
        return blend
    else:
        blend = subnet.copyItems(
            [config_node], channel_reference_originals=True)[0]
        hou.clearAllSelected()
        return blend

