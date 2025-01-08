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
        raise KeyError(
            "Missing required keys in kwargs: 'node' or 'input_index'")

    subnet = kwargs["node"]
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
        print("Could not find inputs or outputs node")
        return
    
    # Clear already existing connection
    for connection in inputs_node.outputConnections():
        if connection.outputIndex() == input_to_connect:
            connection.outputNode().setInput(
                connection.inputIndex(), None)
            
            print("Clear an existing connections")
            break

    # Get every blend node in subnet with mode add
    add_nodes = []
    add_nodes_with_free_input = []
    add_node_connected_to_output  = None

    for child in subnet.children():
        if (child.type().name() == BLENDTYPE)\
            and (child.parm("mode").eval() == ADDMODE):
            add_nodes.append(child)

            # Get every valid input and output
            child_inputs = [input for input in child.inputs()
                             if input is not None]
            child_outputs = [output for output in child.outputs()
                              if output is not None]
            if len(child_inputs) == 1:
                add_nodes_with_free_input.append(child)
            if len(child_outputs) == 1:
                add_node_connected_to_output  = child

    # Check if the input changed was a new connection
    connecting = subnet.input(input_to_connect) is not None

    if not connecting:
        
        # Delete every add node with no connection in input
        cleanAdd(add_nodes)

        # Rewire every node that have only one connection and
        # if that's connection input is fg
        for add_node in add_nodes:
            add_node_inputs = [input for input in add_node.inputs()
                                if input is not None]
            
            if len(add_node_inputs) == 1:
                connection = add_node.inputConnections()[0]
                # If the only connection of the node is on fg
                # Then swap it to bg
                if connection.inputIndex() == 1:
                    add_node.setInput(0,
                                    connection.inputNode(),
                                    connection.outputIndex())
                    add_node.setInput(1, None)

        subnet.layoutChildren()
        return 


    # Try to connect to a node with a free slot
    if add_nodes_with_free_input:
        print("Plug to a free input")

        for input_index, connectors in enumerate(
            add_nodes_with_free_input[0].inputConnectors()):
            if len(connectors) == 0 and input_index != 2:
                add_nodes_with_free_input[0].setInput(
                    input_index, inputs_node, input_to_connect)
                break
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
