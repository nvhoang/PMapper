"""Utility functions that help with querying"""

#  Copyright (c) NCC Group and Erik Steringer 2019. This file is part of Principal Mapper.
#
#      Principal Mapper is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      Principal Mapper is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with Principal Mapper.  If not, see <https://www.gnu.org/licenses/>.

import json
from typing import List

import botocore.session

from principalmapper.common import Edge, Graph, Node
from principalmapper.util import arns


def get_search_list(graph: Graph, node: Node) -> List[List[Edge]]:
    """Returns a list of edge lists. Each edge list represents a path to a new unique node that's accessible from the
    initial node (passed as a param). This is a breadth-first search of nodes from a source node in a graph.
    """
    result = []
    explored_nodes = []

    # run through initial edges
    for edge in get_edges_with_node_source(graph, node, explored_nodes):
        result.append([edge])
    explored_nodes.append(node)

    # dig through result list
    index = 0
    while index < len(result):
        current_node = result[index][-1].destination
        for edge in get_edges_with_node_source(graph, current_node, explored_nodes):
            result.append(result[index][:] + [edge])
        explored_nodes.append(current_node)
        index += 1

    return result


def get_edges_with_node_source(graph: Graph, node: Node, ignored_nodes: List[Node]) -> List[Edge]:
    """Returns a list of nodes that are the destination of edges from the given graph where source of the edge is the
    passed node.
    """
    result = []
    for edge in graph.edges:
        if edge.source == node and edge.destination not in ignored_nodes:
            result.append(edge)
    return result


def is_connected(graph: Graph, source: Node, destination: Node) -> bool:
    """helper function to express if source and node are connected"""
    if source.is_admin:
        return True

    for node_list in get_search_list(graph, source):
        if node_list[-1].destination == destination:
            return True

    return False


def pull_resource_policy_by_arn(session: botocore.session.Session, arn: str) -> dict:
    """helper function for pulling the resource policy for a resource at the denoted ARN.

    raises ValueError if it cannot be retrieved.
    """
    service = arns.get_service(arn)
    if service == 'iam':
        client = session.create_client('iam')
        role_name = arns.get_region(arn).split('/')[-1]
        trust_doc = client.get_role(RoleName=role_name)['Role']['AssumeRolePolicyDocument']
        return json.loads(trust_doc)
    elif service == 's3':
        raise NotImplementedError('Need to implement S3 bucket policy grabbing')
    elif service == 'sns':
        raise NotImplementedError('Need to implement topic policy grabbing')
    elif service == 'sqs':
        raise NotImplementedError('Need to implement queue policy grabbing')
    elif service == 'kms':
        raise NotImplementedError('Need to implement KMS key policy grabbing')
