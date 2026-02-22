"""Enhanced network analysis for fraud pattern detection."""

import logging

logger = logging.getLogger('medicaid_fwa.relationships')


def detect_circular_billing(con, max_hops=3):
    """Detect circular billing patterns (A bills for B, B bills for A).

    Args:
        con: DuckDB connection (read-only).
        max_hops: Maximum cycle length to detect.

    Returns:
        list of dicts describing circular patterns found.
    """
    # Direct reciprocal billing (2-hop cycles)
    rows = con.execute("""
        SELECT
            a.billing_npi AS npi_a,
            a.servicing_npi AS npi_b,
            a.total_paid AS a_to_b_paid,
            b.total_paid AS b_to_a_paid
        FROM billing_servicing_network a
        INNER JOIN billing_servicing_network b
            ON a.billing_npi = b.servicing_npi
            AND a.servicing_npi = b.billing_npi
        WHERE a.billing_npi < a.servicing_npi
        ORDER BY (a.total_paid + b.total_paid) DESC
    """).fetchall()

    patterns = []
    for npi_a, npi_b, a_paid, b_paid in rows:
        patterns.append({
            'type': 'reciprocal',
            'npis': [npi_a, npi_b],
            'total_paid': a_paid + b_paid,
            'a_to_b_paid': a_paid,
            'b_to_a_paid': b_paid,
        })

    logger.info(f'Found {len(patterns)} reciprocal billing pairs')
    return patterns


def detect_hub_and_spoke(con, min_spokes=10, min_total_paid=500000):
    """Detect hub-and-spoke networks (one billing NPI, many servicing).

    Args:
        con: DuckDB connection (read-only).
        min_spokes: Minimum servicing NPIs for hub classification.
        min_total_paid: Minimum total paid across the network.

    Returns:
        list of hub-and-spoke network dicts.
    """
    rows = con.execute(f"""
        SELECT
            billing_npi,
            COUNT(DISTINCT servicing_npi) AS spoke_count,
            SUM(total_paid) AS total_paid,
            SUM(num_claims) AS total_claims
        FROM billing_servicing_network
        WHERE billing_npi != servicing_npi
        GROUP BY billing_npi
        HAVING COUNT(DISTINCT servicing_npi) >= {min_spokes}
            AND SUM(total_paid) >= {min_total_paid}
        ORDER BY spoke_count DESC
    """).fetchall()

    networks = []
    for hub, spokes, paid, claims in rows:
        networks.append({
            'hub_npi': hub,
            'spoke_count': spokes,
            'total_paid': paid,
            'total_claims': claims,
        })

    logger.info(f'Found {len(networks)} hub-and-spoke networks')
    return networks


def compute_network_centrality(G):
    """Compute centrality metrics for nodes in a networkx graph.

    Args:
        G: networkx.DiGraph from relationship_modeler.build_networkx_graph.

    Returns:
        dict mapping npi -> centrality metrics dict, or empty dict if G is None.
    """
    if G is None:
        return {}

    try:
        import networkx as nx
    except ImportError:
        return {}

    degree = nx.degree_centrality(G)
    in_degree = nx.in_degree_centrality(G)
    out_degree = nx.out_degree_centrality(G)

    metrics = {}
    for node in G.nodes():
        metrics[node] = {
            'degree_centrality': degree.get(node, 0),
            'in_degree_centrality': in_degree.get(node, 0),
            'out_degree_centrality': out_degree.get(node, 0),
        }

    logger.info(f'Computed centrality metrics for {len(metrics)} nodes')
    return metrics
