"""Provider relationship graph construction and modeling."""

import logging

logger = logging.getLogger('medicaid_fwa.relationships')


def build_provider_graph(con):
    """Build a directed graph of billing-servicing relationships.

    Args:
        con: DuckDB connection (read-only).

    Returns:
        dict with 'nodes' (set of NPIs) and 'edges' (list of (billing, servicing, weight) tuples).
    """
    rows = con.execute("""
        SELECT billing_npi, servicing_npi, total_paid, num_claims
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        ORDER BY total_paid DESC
    """).fetchall()

    nodes = set()
    edges = []
    for billing, servicing, paid, claims in rows:
        nodes.add(billing)
        nodes.add(servicing)
        edges.append((billing, servicing, {'paid': paid, 'claims': claims}))

    logger.info(f'Built provider graph: {len(nodes)} nodes, {len(edges)} edges')
    return {'nodes': nodes, 'edges': edges}


def build_networkx_graph(graph_data):
    """Convert graph_data dict into a networkx DiGraph.

    Args:
        graph_data: dict from build_provider_graph.

    Returns:
        networkx.DiGraph or None if networkx unavailable.
    """
    try:
        import networkx as nx
    except ImportError:
        logger.warning('networkx not available')
        return None

    G = nx.DiGraph()
    G.add_nodes_from(graph_data['nodes'])
    for billing, servicing, attrs in graph_data['edges']:
        G.add_edge(billing, servicing, **attrs)

    logger.info(f'NetworkX graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
    return G


def get_provider_neighbors(graph_data, npi, direction='both'):
    """Get neighbors of a provider in the relationship graph.

    Args:
        graph_data: dict from build_provider_graph.
        npi: Provider NPI to look up.
        direction: 'billing' (outgoing), 'servicing' (incoming), or 'both'.

    Returns:
        set of connected NPI strings.
    """
    neighbors = set()
    for billing, servicing, _ in graph_data['edges']:
        if direction in ('billing', 'both') and billing == npi:
            neighbors.add(servicing)
        if direction in ('servicing', 'both') and servicing == npi:
            neighbors.add(billing)
    return neighbors
