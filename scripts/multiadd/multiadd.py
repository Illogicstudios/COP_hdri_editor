import hou

BLENDTYPE = "blend"
ADDMODE = 3

def onInputChanged(kwargs):
    """
    Callback on a multi add subnetwork which will adjust the add
    connections.

    More specifically a multi add subnetwork is a basic subnetwork
    where you can add multiples layers in input into a single layer.

    :param kwargs: Subnetwork context
    """

    # Check if the context is correct
    if "node" not in kwargs or "input_index" not in kwargs:
        raise KeyError("Missing required keys in kwargs: 'node' or 'input_index'")

    subnet = kwargs["node"]

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
        print("Could not find inputs or outputs node")
        return

    # Get every blend node in subnet with mode add
    add_nodes = []
    add_node_connected_to_output  = None
    add_node_with_free_input  = None

    for child in subnet.children():
        if (child.type().name() == BLENDTYPE)\
            and (child.parm("mode").eval() == ADDMODE):
            add_nodes.append(child)
            if len(child.outputs()) == 1:
                add_node_connected_to_output  = child
            if len(child.inputs()) == 1:
                add_node_with_free_input  = child

    # Check if the input changed was a new connection
    input_to_connect = kwargs["input_index"]
    connecting = subnet.input(input_to_connect) is not None

    if not connecting:
        for connection in inputs_node.outputConnections():
            if connection.outputIndex() == input_to_connect:
                connection.outputNode().setInput(
                    connection.inputIndex(), None)
                break
        
        # Delete every add node with no connection in input
        cleanAdd(add_nodes)
        subnet.layoutChildren()
        return 


    # Try to connect to a node with a free slot
    if add_node_with_free_input  is not None:
        add_node_with_free_input .setNextInput(inputs_node, input_to_connect)
    # Else add a new blend node with add type
    else:
        if add_node_connected_to_output  is not None:

            outputs_node.setInput(0, None)

            new_add = createAdd(subnet)

            new_add.setInput(0, add_node_connected_to_output , 0)
            new_add.setInput(1, inputs_node, input_to_connect)
            outputs_node.setInput(0, new_add, 0)

        # If there is no blend node with the output node as output
        # we need output our new blend here
        else:
            new_add = createAdd(subnet)
            new_add.setInput(0, inputs_node, 0)
            subnet.subnetOutputs()[0].setInput(0, new_add, 0)

            for add in add_nodes:
                if not len(add.outputs()):
                    add_node_connected_to_output  = add

            if add_node_connected_to_output  is not None:
                new_add.setInput(1, add_node_connected_to_output)
    
    subnet.layoutChildren()
   

def cleanAdd(add_nodes):
    """
    Clean recursively every node that does not have inputs.

    :param add_nodes: List of blend nodes with mode add
    """
    to_delete = [add for add in add_nodes if not add.inputs()]
    while to_delete:
        for add in to_delete:
            add.destroy()
            add_nodes.remove(add)
        to_delete = [add for add in add_nodes if not add.inputs()]


def createAdd(subnet):
    """
    Create a node add with mode add.

    :param subnet: Multi add subnetwork
    """

    add = subnet.createNode(node_type_name=BLENDTYPE)
    add.parm("mode").set(ADDMODE)
    return add
